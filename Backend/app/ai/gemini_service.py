import json
import logging
import re
from typing import List, Dict, Any, Optional
from app.config.settings import get_settings
from app.models.schemas import (
    SourceItem,
    QuizQuestion,
    QuizOption,
    PracticeQuestionItem
)

logger = logging.getLogger("ai_study_assistant.gemini")


class GeminiService:
    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured.")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self._client = None

    def _generate_raw(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Helper to invoke Gemini with primary model and automatic fallback."""
        if not self._client:
            self._init_client()
        if not self._client:
            raise RuntimeError("AI service is temporarily unavailable. Please try again.")

        models_to_try = [self.settings.GEMINI_MODEL] + self.settings.GEMINI_FALLBACK_MODELS
        last_error = None

        for model_name in models_to_try:
            try:
                from google.genai import types
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                )

                resp = self._client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                if resp and resp.text:
                    return resp.text
            except Exception as e:
                logger.warning(f"Gemini generation with {model_name} failed: {e}")
                last_error = e

        raise RuntimeError(f"AI service is temporarily unavailable: {last_error}")

    # ==========================================================
    # ACADEMIC EXPLANATION GENERATOR
    # ==========================================================
    def generate_explanation(
        self,
        question: str,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        explanation_mode: str = "simple",
        web_sources: Optional[List[SourceItem]] = None,
        document_context: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        mode_instructions = {
            "simple": "Explain in plain, beginner-friendly language with an intuitive real-world analogy. Avoid complex jargon unless defined immediately. Keep it engaging and concise.",
            "detailed": "Provide an in-depth academic explanation. Cover theoretical foundations, underlying mechanics/architecture, mathematical definitions or code if relevant, and nuances.",
            "step_by_step": "Provide an ordered, numbered walkthrough explaining each stage sequentially. Include logical transitions and intermediate milestones so the student can follow easily.",
            "revision": "Provide high-yield revision bullet points. Focus on core formulas, key terms, quick contrast tables, and common exam traps.",
            "exam_oriented": "Format in a high-scoring university examination style: Definition, Key Principles/Diagram description, Working Mechanism, Merits & Demerits, and a concluding summary.",
            "examples": "Provide concrete, realistic code snippets or numerical step-by-step worked examples with inputs, outputs, and line-by-line breakdown."
        }

        mode_prompt = mode_instructions.get(explanation_mode.lower(), mode_instructions["simple"])

        system_instruction = (
            "You are the lead academic tutor on 'AI STUDY ASSISTANT' - an intelligent educational platform for students. "
            "Your mission: 'Ask. Understand. Learn. Master.'\n"
            "Guiding Principles:\n"
            "1. Academic Rigor: Ensure technical and scientific accuracy.\n"
            "2. Student-Centric Pedagogy: Teach clearly, concisely, and support understanding.\n"
            "3. Formatting: Use crisp Markdown with headings (##, ###), bullet points, bold key terms, and code blocks with language tags where applicable.\n"
            "4. Grounding & Zero-Hallucination:\n"
            "   - When 'Uploaded Document Context' is provided: Prioritize and ground your answer on it. If page numbers or sections are present, cite them (e.g., [Page X]). If the document does NOT contain enough information to fully answer the question, state that clearly before providing broader academic context.\n"
            "   - When 'Verified Web Learning References' are provided: Draw upon them to enrich the answer and cite verified URLs. Never fabricate fake URLs or citations.\n"
            "   - Clearly distinguish between information sourced from user notes, verified web sources, and general academic concepts."
        )

        prompt_parts = [
            f"### Student Question:\n{question}\n",
            f"Academic Subject: {subject or 'General Academics'}",
            f"Topic: {topic or 'Custom Topic'}",
            f"Target Explanation Style: {mode_prompt}\n"
        ]

        if document_context:
            prompt_parts.append(
                f"### Uploaded Document Context (Base your answer strictly on this content where relevant; cite page/section where indicated):\n"
                f"\"\"\"\n{document_context[:8000]}\n\"\"\"\n"
            )

        if web_sources:
            sources_text = "\n".join([f"- [{s.title}] ({s.url}) - {s.description}" for s in web_sources[:4]])
            prompt_parts.append(
                f"### Verified Web Learning References (Use these real findings to enrich the explanation):\n"
                f"{sources_text}\n"
            )

        if chat_history:
            history_text = "\n".join([f"{m.get('role', 'USER')}: {m.get('content', '')}" for m in chat_history[-4:]])
            prompt_parts.append(
                f"### Recent Conversation Context:\n{history_text}\n"
            )

        prompt_parts.append("\nPlease deliver the explanation now in clean, structured Markdown:")

        full_prompt = "\n".join(prompt_parts)
        return self._generate_raw(full_prompt, system_instruction=system_instruction)

    # ==========================================================
    # STUDY TOOLS: SUMMARIZE
    # ==========================================================
    def summarize(self, content: str, topic: Optional[str] = None) -> str:
        prompt = (
            f"Please generate a comprehensive, high-retention academic summary of the following study material.\n"
            f"Topic: {topic or 'Academic Study'}\n\n"
            f"Material:\n\"\"\"\n{content[:6000]}\n\"\"\"\n\n"
            f"Format requirements:\n"
            f"1. **Core Concept in One Sentence**\n"
            f"2. **Key Takeaways** (3 to 6 high-yield bullet points)\n"
            f"3. **Crucial Terminology & Definitions**\n"
            f"4. **Quick Revision Cheat-Sheet**\n"
        )
        return self._generate_raw(prompt)

    # ==========================================================
    # STUDY TOOLS: GENERATE STUDY NOTES
    # ==========================================================
    def generate_notes(self, topic: str, subject: Optional[str] = None, document_context: Optional[str] = None) -> str:
        prompt = (
            f"Generate structured, publication-grade academic study notes on the topic:\n"
            f"Topic: {topic}\n"
            f"Subject: {subject or 'Computer Science / Engineering'}\n\n"
        )
        if document_context:
            prompt += f"Document Reference:\n\"\"\"\n{document_context[:4000]}\n\"\"\"\n\n"

        prompt += (
            "Structure the notes with:\n"
            "# {Topic Title}\n"
            "## 1. Overview & Core Motivation\n"
            "## 2. Fundamental Principles & Architecture\n"
            "## 3. Step-by-Step Mechanisms / Mathematical Formulas / Code Algorithms\n"
            "## 4. Real-World Applications & Case Studies\n"
            "## 5. Common Pitfalls & Edge Cases\n"
            "## 6. Exam / Interview High-Yield Checklist\n"
        )
        return self._generate_raw(prompt)

    # ==========================================================
    # STUDY TOOLS: GENERATE QUIZ (JSON)
    # ==========================================================
    def generate_quiz(self, topic: str, count: int = 5, difficulty: str = "medium", document_context: Optional[str] = None) -> List[QuizQuestion]:
        prompt = (
            f"Generate an academic multiple-choice quiz of exactly {count} questions on the topic: '{topic}'.\n"
            f"Difficulty level: {difficulty}.\n"
        )
        if document_context:
            prompt += f"Base the questions primarily on this document context:\n\"\"\"\n{document_context[:3500]}\n\"\"\"\n"

        prompt += (
            "Return ONLY valid JSON without markdown wrapping or code fences. Follow this exact JSON structure:\n"
            "[\n"
            "  {\n"
            '    "id": 1,\n'
            '    "question": "What is ...?",\n'
            '    "options": [\n'
            '      {"key": "A", "text": "First option"},\n'
            '      {"key": "B", "text": "Second option"},\n'
            '      {"key": "C", "text": "Third option"},\n'
            '      {"key": "D", "text": "Fourth option"}\n'
            "    ],\n"
            '    "correct_answer": "B",\n'
            '    "explanation": "Detailed pedagogical explanation for why B is correct and why other options are wrong."\n'
            "  }\n"
            "]"
        )

        raw = self._generate_raw(prompt)
        cleaned = re.sub(r"^```json\s*", "", raw.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            items = json.loads(cleaned)
            questions: List[QuizQuestion] = []
            for item in items:
                opts = [QuizOption(key=o["key"], text=o["text"]) for o in item.get("options", [])]
                questions.append(QuizQuestion(
                    id=item.get("id", len(questions) + 1),
                    question=item.get("question", ""),
                    options=opts,
                    correct_answer=item.get("correct_answer", "A"),
                    explanation=item.get("explanation", "")
                ))
            return questions
        except Exception as e:
            logger.error(f"Failed to parse quiz JSON: {e}. Raw text: {raw[:300]}")
            # Safe structured fallback
            return [
                QuizQuestion(
                    id=1,
                    question=f"Which fundamental principle is central to understanding {topic}?",
                    options=[
                        QuizOption(key="A", text="Systematic decomposition and logical invariant checking"),
                        QuizOption(key="B", text="Arbitrary execution without boundary conditions"),
                        QuizOption(key="C", text="Linear extrapolation without state tracking"),
                        QuizOption(key="D", text="Ignoring algorithmic complexity")
                    ],
                    correct_answer="A",
                    explanation=f"In academic study of {topic}, rigorous decomposition and invariants provide the formal guarantee of correctness."
                )
            ]

    # ==========================================================
    # STUDY TOOLS: PRACTICE QUESTIONS
    # ==========================================================
    def generate_practice_questions(self, topic: str, count: int = 5, document_context: Optional[str] = None) -> List[PracticeQuestionItem]:
        prompt = (
            f"Generate exactly {count} academic practice questions for students learning '{topic}'.\n"
            f"Mix question types: Conceptual, Problem-Solving, Exam-Style, and Analysis.\n"
        )
        if document_context:
            prompt += f"Material Context:\n\"\"\"\n{document_context[:3500]}\n\"\"\"\n"

        prompt += (
            "Return ONLY valid JSON without markdown wrapping. Format:\n"
            "[\n"
            "  {\n"
            '    "id": 1,\n'
            '    "type": "Conceptual",\n'
            '    "question": "Question text...",\n'
            '    "hints": ["Hint 1", "Hint 2"],\n'
            '    "model_answer": "Complete, high-scoring model answer with steps."\n'
            "  }\n"
            "]"
        )

        raw = self._generate_raw(prompt)
        cleaned = re.sub(r"^```json\s*", "", raw.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            items = json.loads(cleaned)
            questions: List[PracticeQuestionItem] = []
            for item in items:
                questions.append(PracticeQuestionItem(
                    id=item.get("id", len(questions) + 1),
                    type=item.get("type", "Conceptual"),
                    question=item.get("question", ""),
                    hints=item.get("hints", []),
                    model_answer=item.get("model_answer", "")
                ))
            return questions
        except Exception as e:
            logger.error(f"Failed to parse practice questions JSON: {e}")
            return [
                PracticeQuestionItem(
                    id=1,
                    type="Conceptual",
                    question=f"Analyze the core mechanics and trade-offs of {topic}.",
                    hints=["Consider space and time complexity", "Identify standard edge cases"],
                    model_answer=f"When analyzing {topic}, the primary trade-offs include memory overhead versus computational latency."
                )
            ]


_gemini_instance: Optional[GeminiService] = None

def get_gemini_service() -> GeminiService:
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiService()
    return _gemini_instance
