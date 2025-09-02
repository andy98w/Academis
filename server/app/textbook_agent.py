import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

class TextbookGenerationAgent:
    
    def __init__(self):
        self.model = ChatOpenAI(model_name="gpt-4o", temperature=0.3)
        self.search_tool = self._initialize_search()
        self.rag_initialized = False
    
    def _get_chapter_specific_topics(self, chapter: str, chapter_title: str, subject: str = "micro") -> str:
        from .helpers import get_chapter_specific_topics
        return get_chapter_specific_topics(chapter, chapter_title, subject)
        
    def _initialize_search(self) -> Optional[TavilySearchResults]:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if tavily_api_key:
            try:
                return TavilySearchResults(max_results=3)
            except Exception as e:
                logger.warning(f"Could not initialize Tavily search: {e}")
                return None
        else:
            logger.info("TAVILY_API_KEY not set - web search will be disabled")
            return None
    
    async def search_web(self, query: str) -> str:
        if not self.search_tool:
            return ""
        
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                None, self.search_tool.run, query
            )
            
            if isinstance(results, list):
                # Format results into a readable string
                formatted_results = []
                for result in results[:3]:  # Limit to top 3 results
                    if isinstance(result, dict):
                        content = result.get('content', '')
                        if content:
                            formatted_results.append(content)
                return "\n\n".join(formatted_results)
            elif isinstance(results, str):
                return results
            else:
                return ""
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return ""
    
    async def retrieve_authoritative_content(self, chapter_title: str, chapter_topics: str) -> str:
        try:
            from .rag_service import get_rag_response, initialize_vector_store
            
            if not self.rag_initialized:
                await initialize_vector_store()
                self.rag_initialized = True
            
            # Extract just the topic names for filtering
            topic_lines = chapter_topics.split('\n')
            topic_keywords = []
            for line in topic_lines:
                if line.strip().startswith('- '):
                    # Extract the main topic before the colon
                    topic_part = line.strip()[2:].split(':')[0].lower()
                    topic_keywords.append(topic_part)
            
            # Create strict RAG query using only the chapter topics
            rag_query = f"""Find content ONLY about these specific topics for {chapter_title}:
{chapter_topics}

STRICT REQUIREMENTS:
- ONLY include content directly related to the topics listed above
- DO NOT include any topics not explicitly listed
- DO NOT include content from other chapters
- Focus on definitions, examples, and explanations of ONLY the listed concepts"""
            
            session_id = f"textbook_rag_{chapter_title.replace(' ', '_').lower()}"
            rag_content = await get_rag_response(rag_query, session_id, use_history=False)
            
            # Filter the retrieved content to remove off-topic material
            if isinstance(rag_content, dict):
                content = rag_content.get('text', '')
            else:
                content = str(rag_content)
            
            # Dynamic filtering based on chapter topics keywords
            topic_keywords = []
            excluded_terms = []
            
            # Extract allowed keywords from our chapter topics
            for line in topic_lines:
                if line.strip().startswith('- '):
                    topic_text = line.strip()[2:].lower()
                    if ':' in topic_text:
                        main_concept = topic_text.split(':')[0].strip()
                        description = topic_text.split(':')[1].strip()
                        topic_keywords.extend([main_concept])
                        # Add important descriptive words
                        desc_words = [w for w in description.split() if len(w) > 3][:4]
                        topic_keywords.extend(desc_words)
                    else:
                        topic_keywords.extend([w for w in topic_text.split() if len(w) > 3])
            
            # No hardcoded exclusions - rely purely on positive filtering for allowed topics
            
            # Pure positive filtering - only keep content that relates to our chapter topics
            if topic_keywords:
                filtered_sentences = []
                for sentence in content.split('.'):
                    sentence_lower = sentence.lower().strip()
                    if len(sentence_lower) < 10:  # Skip very short fragments
                        continue
                    
                    # Only keep sentences that contain our chapter-specific keywords
                    has_topic_keyword = any(keyword in sentence_lower for keyword in topic_keywords if len(keyword) > 3)
                    if has_topic_keyword:
                        filtered_sentences.append(sentence)
                
                content = '. '.join(filtered_sentences)
            
            return content
                
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return ""
    
    async def generate_content_outline(self, subject: str, chapter_title: str, chapter_number: str = None) -> Dict[str, Any]:
        """First pass: Generate a detailed outline for the chapter with chapter-specific focus"""
        
        # Get chapter-specific topics to ensure focused content
        chapter_specific_topics = self._get_chapter_specific_topics(chapter_number or "", chapter_title)
        
        prompt = ChatPromptTemplate.from_template("""
        Create a focused outline for chapter "{chapter_title}" in {subject}.
        
        CRITICAL: Cover ONLY these specific topics and NOTHING MORE:
        {chapter_topics}
        
        STRICT REQUIREMENTS:
        - Do NOT include any topics not listed above
        - Do NOT add related concepts from other chapters
        - Do NOT expand beyond the specified scope
        - Stay strictly within the boundaries of what is listed
        - Create ONLY ONE Introduction section, not multiple intros
        
        VISUALIZATION DETECTION:
        - If topics mention: "curve", "graph", "chart", "model", "diagram", then visualizations are REQUIRED
        - Look for mathematical relationships, comparisons, or trade-offs that need visual representation
        - Consider if the concept would be difficult to understand without a visual aid
        
        Return a JSON object with the following structure:
        {{
            "key_concepts": ["list of concepts ONLY from the specified topics"],
            "learning_objectives": ["list of 2-3 objectives based ONLY on specified topics"],
            "sections": [
                {{
                    "title": "Introduction",
                    "topics": ["Brief overview of chapter focus and importance"],
                    "examples_needed": ["Real-world context examples"]
                }},
                {{
                    "title": "section title for main concepts",
                    "topics": ["ONLY topics from the specified list"],
                    "examples_needed": ["examples that illustrate ONLY the specified concepts"]
                }}
            ],
            "visualizations_needed": ["CRITICAL: Analyze the topics above. If ANY topic mentions or implies visual elements (graphs, charts, curves, models, diagrams, visual representations, relationships between variables), you MUST list them here. Leave empty ONLY if topics are purely conceptual with no visual components."],
            "practice_problems": ["problems testing ONLY the specified concepts"]
        }}
        
        Return ONLY valid JSON.
        """)
        
        chain = prompt | self.model | StrOutputParser()
        
        try:
            response = await chain.ainvoke({
                "subject": subject,
                "chapter_title": chapter_title,
                "chapter_topics": chapter_specific_topics
            })
            
            import json
            # Clean up the response to ensure valid JSON
            response = response.strip()
            # Remove any markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating outline: {e}")
            return {
                "key_concepts": [chapter_title],
                "learning_objectives": ["Understand " + chapter_title],
                "sections": [{"title": "Overview", "topics": [chapter_title], "examples_needed": ["General examples"]}],
                "visualizations_needed": [],
                "practice_problems": ["Conceptual questions"]
            }
    
    async def enrich_with_current_info(self, topic: str, subject: str) -> str:
        """Search for current information and examples about the topic"""
        
        if not self.search_tool:
            return ""
        
        # Create targeted search queries
        queries = [
            f"{topic} {subject} current examples 2024",
            f"{topic} real world applications recent",
            f"{topic} case studies analysis"
        ]
        
        all_results = []
        for query in queries:
            result = await self.search_web(query)
            if result:
                all_results.append(result)
        
        return "\n\n".join(all_results)
    
    async def generate_section_content(self, section: Dict[str, Any], subject: str, 
                                      chapter_title: str, web_context: str = "", 
                                      authoritative_content: str = "") -> str:
        """Generate content for a specific section with web enrichment"""
        
        prompt = ChatPromptTemplate.from_template("""
        Write a focused educational section about "{section_title}" for the chapter "{chapter_title}" in {subject}.
        
        Topics to cover (ONLY these topics):
        {topics}
        
        Examples to include:
        {examples}
        
        Authoritative content from AP textbooks (use as foundation):
        {authoritative_content}
        
        Current information and examples (for supplementation):
        {web_context}
        
        INSTRUCTIONS:
        1. Base your content on the authoritative textbook content above
        2. Enhance with current examples and information where appropriate  
        3. Cover ONLY the topics listed - do NOT introduce concepts from other chapters
        4. Write 2-4 focused paragraphs, each 3-5 sentences
        5. Use **bold** for key terms when first introduced
        6. Include specific examples that illustrate the listed topics
        7. Maintain academic rigor while being accessible
        8. Stay strictly within the chapter's boundaries
        
        Content:
        """)
        
        topics = "\n".join(f"- {topic}" for topic in section.get("topics", []))
        examples = "\n".join(f"- {ex}" for ex in section.get("examples_needed", []))
        
        chain = prompt | self.model | StrOutputParser()
        
        response = await chain.ainvoke({
            "section_title": section.get("title", ""),
            "chapter_title": chapter_title,
            "subject": subject,
            "topics": topics,
            "examples": examples,
            "authoritative_content": authoritative_content[:3000] if authoritative_content else "No authoritative content retrieved",
            "web_context": web_context[:2000] if web_context else "No current information available"
        })
        
        return response
    
    async def generate_practice_problems(self, chapter_title: str, subject: str, 
                                        key_concepts: List[str]) -> str:
        """Generate practice problems with solutions"""
        
        prompt = ChatPromptTemplate.from_template("""
        Create 4 AP-style practice problems for the chapter "{chapter_title}" in {subject}.
        
        Key concepts to test:
        {concepts}
        
        REQUIREMENTS:
        - Mix of multiple choice and free response questions
        - Clear, specific questions that test understanding
        - Realistic scenarios and examples
        - Appropriate difficulty for AP level
        
        Format EXACTLY as follows:
        
        **Question 1:** [Clear, specific question with proper question mark]
        A) [Option A]
        B) [Option B] 
        C) [Option C]
        D) [Option D]
        
        **Answer:** [Letter] - [Brief explanation of why this answer is correct]
        
        **Question 2:** [Free response question requiring explanation or analysis]
        
        **Answer:** [Complete explanation with key points and reasoning]
        
        Continue this pattern for all 4 questions. NO dashes, lines, or extra formatting.
        Make questions specific and testable, not just topic names.
        """)
        
        concepts = "\n".join(f"- {concept}" for concept in key_concepts)
        
        chain = prompt | self.model | StrOutputParser()
        
        return await chain.ainvoke({
            "chapter_title": chapter_title,
            "subject": subject,
            "concepts": concepts
        })
    
    async def generate_enhanced_textbook_content(self, subject: str, chapter_title: str,
                                                 use_web_search: bool = True) -> List[str]:
        """
        Generate high-quality textbook content using multiple passes and web enrichment
        
        Args:
            subject: The subject area (e.g., "AP Biology", "AP Chemistry", "AP History")
            chapter_title: The chapter title (format: "1.1: Title" or just "Title")
            use_web_search: Whether to use web search for enrichment
            
        Returns:
            List of paragraphs with enhanced content
        """
        
        logger.info(f"Starting enhanced generation for {chapter_title}")
        
        # Extract chapter number if present
        chapter_number = ""
        if ":" in chapter_title:
            chapter_number = chapter_title.split(":")[0].strip()
        
        # Step 1: Generate focused outline
        outline = await self.generate_content_outline(subject, chapter_title, chapter_number)
        logger.info(f"Generated outline with {len(outline.get('sections', []))} sections")
        
        # Step 1.5: Force visualization detection if topics contain visual terms
        chapter_topics = self._get_chapter_specific_topics(chapter_number, chapter_title, "micro")
        topics_text = chapter_topics.lower()
        visual_terms = ['curve', 'graph', 'chart', 'model', 'diagram', 'visual', 'showing']
        
        if any(term in topics_text for term in visual_terms) and not outline.get("visualizations_needed"):
            logger.info("Force-adding visualization because topics contain visual terms")
            outline["visualizations_needed"] = [f"Visual representation for {chapter_title} concepts"]
        
        # Step 2: Search for current information if enabled
        web_context = ""
        if use_web_search and self.search_tool:
            logger.info("Searching for current information...")
            web_context = await self.enrich_with_current_info(chapter_title, subject)
            if web_context:
                logger.info(f"Found {len(web_context)} characters of web content")
        
        # Step 2.5: Retrieve authoritative content from Princeton Review PDFs
        chapter_topics = self._get_chapter_specific_topics(chapter_number, chapter_title, "micro")
        logger.info("Retrieving authoritative content from textbooks...")
        authoritative_content = await self.retrieve_authoritative_content(chapter_title, chapter_topics)
        if authoritative_content:
            logger.info(f"Found {len(authoritative_content)} characters of authoritative content")
        
        # Step 3: Generate content for each section
        all_paragraphs = []
        
        # Generate main sections (including the Introduction from outline)
        for section in outline.get("sections", []):
            section_title = section.get("title", "")
            if section_title:
                all_paragraphs.append(f"## {section_title}")
                
                # Get section-specific web context if available
                section_web_context = ""
                if use_web_search and self.search_tool:
                    section_query = f"{chapter_title} {section_title}"
                    section_web_context = await self.search_web(section_query)
                
                content = await self.generate_section_content(
                    section, subject, chapter_title, 
                    section_web_context or web_context,
                    authoritative_content
                )
                all_paragraphs.extend(content.split("\n\n"))
        
        # Add visualization section if needed
        if outline.get("visualizations_needed"):
            # Use a more dynamic title based on chapter content
            viz_section_title = "Visual Models and Analysis" if "model" in chapter_title.lower() else "Charts and Graphs"
            all_paragraphs.append(f"## {viz_section_title}")
            
            # Generate description of models
            model_prompt = ChatPromptTemplate.from_template("""
            Describe the conceptual models and visual representations relevant to {chapter_title}.
            
            Visualizations/models to explain:
            {visualizations}
            
            For each model:
            - Explain what it represents
            - Describe the axes and curves
            - Explain how to interpret it
            - Add [GRAPH:description] where the visualization should appear
            
            Write 3-4 detailed paragraphs.
            """)
            
            visualizations = "\n".join(f"- {viz}" for viz in outline.get("visualizations_needed", []))
            
            chain = model_prompt | self.model | StrOutputParser()
            model_content = await chain.ainvoke({
                "chapter_title": chapter_title,
                "visualizations": visualizations
            })
            all_paragraphs.extend(model_content.split("\n\n"))
        
        # Add practice problems with proper formatting for frontend
        all_paragraphs.append("## Review Questions")
        problems = await self.generate_practice_problems(
            chapter_title, subject, 
            outline.get("key_concepts", [])
        )
        
        # Add practice problems with clean formatting
        problem_lines = problems.split("\n")
        current_block = []
        
        for line in problem_lines:
            line = line.strip()
            if not line:
                if current_block:
                    block_text = "\n".join(current_block)
                    if block_text:
                        all_paragraphs.append(block_text)
                    current_block = []
            else:
                # Remove any trailing dashes or unwanted formatting
                clean_line = line.rstrip("- \t")
                current_block.append(clean_line)
        
        # Add final block if exists
        if current_block:
            block_text = "\n".join(current_block)
            if block_text:
                all_paragraphs.append(block_text)
        
        # Add conclusion/summary
        all_paragraphs.append("## Summary")
        
        summary_prompt = ChatPromptTemplate.from_template("""
        Write a comprehensive summary for the chapter on {chapter_title}.
        
        Key concepts covered:
        {concepts}
        
        Learning objectives:
        {objectives}
        
        Start with "**Key Takeaways:** " and then provide a 2-3 paragraph summary that:
        - Reinforces the main concepts
        - Connects ideas together
        - Explains practical significance
        - Prepares students for assessments
        """)
        
        chain = summary_prompt | self.model | StrOutputParser()
        summary = await chain.ainvoke({
            "chapter_title": chapter_title,
            "concepts": "\n".join(f"- {c}" for c in outline.get("key_concepts", [])),
            "objectives": "\n".join(f"- {o}" for o in outline.get("learning_objectives", []))
        })
        all_paragraphs.extend(summary.split("\n\n"))
        
        # Filter out empty paragraphs
        all_paragraphs = [p.strip() for p in all_paragraphs if p.strip()]
        
        logger.info(f"Generated {len(all_paragraphs)} paragraphs of enhanced content")
        return all_paragraphs

# Global instance
textbook_agent = TextbookGenerationAgent()