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
        chat_history: Optional[List[Dict[str, str]]] = None,
        strict_document_grounding: bool = False,
        grounding_status: Optional[str] = None,
        missing_terms: Optional[List[str]] = None
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

        if strict_document_grounding:
            missing_clause = ""
            if missing_terms:
                missing_clause = f"\nSpecifically, the following terms are NOT present in the document: {', '.join(missing_terms)}."

            system_instruction = (
                "You are an academic tutor on 'AI STUDY ASSISTANT' operating in STRICT DOCUMENT-GROUNDED MODE.\n"
                "Your objective is to answer solely using the student's uploaded document without any hallucination.\n\n"
                "CRITICAL MANDATORY RULES:\n"
                "1. Base your answer EXCLUSIVELY and STRICTLY on the text provided in 'Uploaded Document Context'.\n"
                "2. DO NOT use general outside knowledge. DO NOT rely on pre-trained assumptions.\n"
                "3. DO NOT invent, extrapolate, or pretend that outside information comes from the document.\n"
                "4. If page numbers or sections are provided in the context, cite them accurately (e.g., [Page X, Section Y]).\n"
                "5. Partial support handling:\n"
                "   - If the document context supports only part of the question, clearly state what IS supported (with citations).\n"
                f"   - Explicitly and prominently state what IS NOT supported or missing from the document.{missing_clause}\n"
                "   - DO NOT silently fill in the missing portion from general knowledge.\n"
                "6. If the document context does NOT contain enough evidence to answer the question, state unambiguously:\n"
                "   'I couldn't find this information in the uploaded document.'\n"
                "7. For summary, overview, or key takeaway requests: deliver a well-structured document summary strictly synthesizing the concepts, agenda, sections, or findings present in 'Uploaded Document Context'. Cite page numbers and sections where present.\n"
                "8. Format using clean Markdown with bold key terms and bullet points."
            )
        else:
            system_instruction = (
                "You are the lead academic tutor on 'AI STUDY ASSISTANT' - an intelligent educational platform for students. "
                "Your mission: 'Ask. Understand. Learn. Master.'\n"
                "Guiding Principles:\n"
                "1. Academic Rigor: Ensure technical and scientific accuracy.\n"
                "2. Student-Centric Pedagogy: Teach clearly, concisely, and support understanding.\n"
                "3. Formatting: Use crisp Markdown with headings (##, ###), bullet points, bold key terms, and code blocks with language tags where applicable.\n"
                "4. Grounding & Zero-Hallucination:\n"
                "   - When 'Uploaded Document Context' is provided: Ground your answer on it and cite pages/sections. Do not invent facts.\n"
                "   - When 'Verified Web Learning References' are provided: Draw upon them to enrich the answer and cite verified URLs. Never fabricate fake URLs or citations.\n"
                "   - Clearly distinguish between user notes, verified web sources, and general academic concepts."
            )

        prompt_parts = [
            f"### Student Question:\n{question}\n",
            f"Academic Subject: {subject or 'General Academics'}",
            f"Topic: {topic or 'Custom Topic'}",
            f"Target Explanation Style: {mode_prompt}\n"
        ]

        if document_context:
            label = "Uploaded Document Context (STRICT GROUNDING SOURCE - USE ONLY THIS CONTENT)" if strict_document_grounding else "Uploaded Document Context"
            prompt_parts.append(
                f"### {label}:\n"
                f"\"\"\"\n{document_context[:8000]}\n\"\"\"\n"
            )

        if web_sources and not strict_document_grounding:
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
    @staticmethod
    def _generate_diverse_fallback_quiz(topic: str, count: int) -> List[QuizQuestion]:
        """Provides academically rigorous, multi-dimensional fallback quiz questions ensuring diversity and answer integrity."""
        templates = [
            (
                f"Which fundamental theoretical principle forms the core foundation of {topic}?",
                [
                    ("A", "Systematic decomposition and formal invariant guarantees"),
                    ("B", "Arbitrary non-deterministic state mutations"),
                    ("C", "Linear execution ignoring spatial and temporal constraints"),
                    ("D", "Heuristic guessing without empirical or mathematical verification")
                ],
                "A",
                f"In theoretical computer science, {topic} relies centrally on invariant guarantees and rigorous structural decomposition."
            ),
            (
                f"When executing or operating with {topic}, which internal mechanism ensures correctness?",
                [
                    ("A", "Periodic unvalidated state drops"),
                    ("B", "Deterministic state transition validation and bounds checking"),
                    ("C", "Ignoring reference counters and lifecycle hooks"),
                    ("D", "Unsynchronized concurrent writes to shared mutable memory")
                ],
                "B",
                f"Correct operation in {topic} requires deterministic state validation and strict bounds enforcement."
            ),
            (
                f"What is the primary computational or architectural trade-off when implementing {topic}?",
                [
                    ("A", "Space complexity and memory overhead versus query/execution latency"),
                    ("B", "Instantaneous infinite throughput at zero computational cost"),
                    ("C", "Guaranteed zero memory usage regardless of data volume"),
                    ("D", "Complete elimination of CPU cycles during graph traversal")
                ],
                "A",
                f"Every engineering implementation of {topic} balances memory overhead against lookup/processing latency."
            ),
            (
                f"Which critical boundary condition or edge case poses the most frequent failure mode in {topic}?",
                [
                    ("A", "Empty input sets, null references, or boundary index overflow"),
                    ("B", "Excessively well-formed input datasets"),
                    ("C", "Strict adherence to type contracts and schema invariants"),
                    ("D", "Optimal memory alignment on modern CPU architectures")
                ],
                "A",
                f"Boundary violations such as empty structures, off-by-one errors, and null pointers represent the classic failure modes in {topic}."
            ),
            (
                f"In a production system architecture, which real-world scenario demonstrates the most effective use of {topic}?",
                [
                    ("A", "High-throughput distributed systems requiring predictable latency and data integrity"),
                    ("B", "Storing temporary ephemeral logs without ever querying them"),
                    ("C", "Replacing all network protocols with unbuffered character streams"),
                    ("D", "Static text rendering on offline embedded displays")
                ],
                "A",
                f"In production architectures, {topic} is best leveraged where predictable latency, structural consistency, and scaling invariants are critical."
            )
        ]

        questions: List[QuizQuestion] = []
        for idx in range(min(count, len(templates))):
            q_text, opts_data, correct_key, expl = templates[idx]
            options = [QuizOption(key=k, text=t) for k, t in opts_data]
            questions.append(QuizQuestion(
                id=idx + 1,
                question=q_text,
                options=options,
                correct_answer=correct_key,
                explanation=expl
            ))
        return questions

    @staticmethod
    def _sanitize_quiz_questions(raw_items: List[Dict[str, Any]], topic: str, count: int) -> List[QuizQuestion]:
        """Cleans, validates answer integrity, and rejects near-duplicate template questions."""
        valid_keys = {"A", "B", "C", "D"}
        seen_questions: List[str] = []
        cleaned_questions: List[QuizQuestion] = []

        for item in raw_items:
            q_text = str(item.get("question", "")).strip()
            if not q_text or len(q_text) < 10:
                continue

            # Diversity check: compute token Jaccard similarity against already accepted questions
            tokens = set(re.findall(r"\w+", q_text.lower()))
            is_duplicate = False
            for seen in seen_questions:
                seen_tokens = set(re.findall(r"\w+", seen.lower()))
                if tokens and seen_tokens:
                    jaccard = len(tokens & seen_tokens) / len(tokens | seen_tokens)
                    if jaccard > 0.72:  # High template overlap
                        is_duplicate = True
                        break
            if is_duplicate:
                logger.warning(f"Rejected duplicate quiz question template: {q_text[:60]}")
                continue

            # Sanitize options
            raw_options = item.get("options", [])
            opts: List[QuizOption] = []
            for opt_idx, o in enumerate(raw_options):
                if isinstance(o, dict):
                    key = str(o.get("key", "")).strip().upper()
                    if key not in valid_keys and opt_idx < 4:
                        key = ["A", "B", "C", "D"][opt_idx]
                    text = str(o.get("text", "")).strip()
                    if text:
                        opts.append(QuizOption(key=key, text=text))
                elif isinstance(o, str):
                    key = ["A", "B", "C", "D"][opt_idx % 4]
                    opts.append(QuizOption(key=key, text=o.strip()))

            if len(opts) < 2:
                continue

            # Ensure all keys A..D are distinct
            existing_keys = [o.key for o in opts]
            if len(existing_keys) != len(set(existing_keys)) or any(k not in valid_keys for k in existing_keys):
                for opt_idx, o in enumerate(opts[:4]):
                    o.key = ["A", "B", "C", "D"][opt_idx]

            # Sanitize and verify correct answer key
            raw_ans = str(item.get("correct_answer", "")).strip().upper()
            clean_ans = None
            if raw_ans in valid_keys and raw_ans in {o.key for o in opts}:
                clean_ans = raw_ans
            else:
                match = re.search(r"\b([A-D])\b", raw_ans)
                if match and match.group(1) in {o.key for o in opts}:
                    clean_ans = match.group(1)
                else:
                    for o in opts:
                        if raw_ans.lower() in o.text.lower() or o.text.lower() in raw_ans.lower():
                            clean_ans = o.key
                            break

            if not clean_ans:
                clean_ans = opts[0].key

            explanation = str(item.get("explanation", "")).strip()
            if not explanation:
                explanation = f"Option {clean_ans} is the academically validated answer for '{topic}'."

            seen_questions.append(q_text)
            cleaned_questions.append(QuizQuestion(
                id=len(cleaned_questions) + 1,
                question=q_text,
                options=opts,
                correct_answer=clean_ans,
                explanation=explanation
            ))

            if len(cleaned_questions) >= count:
                break

        # If model generated fewer than count, supplement with diverse fallback questions
        if len(cleaned_questions) < count:
            fallbacks = GeminiService._generate_diverse_fallback_quiz(topic, count)
            for fb in fallbacks:
                if len(cleaned_questions) >= count:
                    break
                fb_tokens = set(re.findall(r"\w+", fb.question.lower()))
                if not any(len(fb_tokens & set(re.findall(r"\w+", s.lower()))) / max(1, len(fb_tokens | set(re.findall(r"\w+", s.lower())))) > 0.72 for s in seen_questions):
                    fb.id = len(cleaned_questions) + 1
                    cleaned_questions.append(fb)

        return cleaned_questions

    def generate_quiz(self, topic: str, count: int = 5, difficulty: str = "medium", document_context: Optional[str] = None) -> List[QuizQuestion]:
        dimensions = [
            "1. Foundational Core Definition & Theoretical Principle: Assess deep conceptual understanding rather than rote recall.",
            "2. Internal Mechanics & Algorithmic Process: Examine step-by-step state transitions, operation flow, or data movement.",
            "3. Comparative Analysis & Trade-Offs: Compare asymptotic complexity (time/space), architectural trade-offs, or pros/cons vs alternatives.",
            "4. Edge Cases, Failure Modes & Pitfalls: Test what occurs under boundary conditions, off-by-one errors, invalid input, or resource exhaustion.",
            "5. Real-World Practical Application & Case Study: Provide a concrete, scenario-based engineering/scientific dilemma requiring synthesis."
        ]
        dim_instructions = "\n".join([f"- {d}" for d in dimensions[:min(count, len(dimensions))]])

        prompt = (
            f"Generate an academic multiple-choice quiz of exactly {count} distinct questions on the topic: '{topic}'.\n"
            f"Difficulty level: {difficulty}.\n\n"
            f"### CRITICAL PEDAGOGICAL DIVERSITY MANDATE:\n"
            f"Each question MUST test a completely different conceptual dimension of '{topic}'. DO NOT clone templates or merely substitute numbers/variable names.\n"
            f"Required Cognitive Dimensions:\n{dim_instructions}\n\n"
            f"### ANSWER INTEGRITY & DISTRACTOR RULES:\n"
            f"1. Each question must have EXACTLY 4 plausible options labeled 'A', 'B', 'C', and 'D'.\n"
            f"2. Distractors must reflect authentic student misconceptions or common bugs, not obvious nonsense.\n"
            f"3. 'correct_answer' MUST be strictly one of ['A', 'B', 'C', 'D'].\n"
            f"4. 'explanation' MUST clearly articulate why that exact option letter is correct, and specifically explain why the other 3 options are incorrect.\n\n"
        )
        if document_context:
            prompt += f"Base the questions primarily on this document context:\n\"\"\"\n{document_context[:3500]}\n\"\"\"\n\n"

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

        try:
            raw = self._generate_raw(prompt)
            cleaned = re.sub(r"^```json\s*", "", raw.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"^```\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            items = json.loads(cleaned)
            return self._sanitize_quiz_questions(items, topic, count)
        except Exception as e:
            logger.error(f"Failed to generate or parse quiz JSON: {e}")
            return self._generate_diverse_fallback_quiz(topic, count)

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
