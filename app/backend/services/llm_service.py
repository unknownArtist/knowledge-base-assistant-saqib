import asyncio
import re
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import os
from config.settings import settings


class LLMService:
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.max_tokens = 4000  # Context window limit
        self.approx_tokens_per_char = 0.25  # Rough estimation: 4 chars per token
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using character-based approximation"""
        return int(len(text) * self.approx_tokens_per_char)
    
    def chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into chunks, respecting word boundaries"""
        if self.estimate_tokens(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = self.estimate_tokens(word + " ")
            if current_size + word_size > max_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def summarize_context(self, articles: List[Dict[str, Any]]) -> str:
        """Summarize long context using LLM if needed"""
        total_content = ""
        for article in articles:
            total_content += f"Title: {article.get('title', '')}\n"
            total_content += f"Content: {article.get('content', '')}\n\n"
        
        if self.estimate_tokens(total_content) <= self.max_tokens:
            return total_content
        
        # If context is too long, summarize it
        prompt = f"""Please summarize the following articles concisely while preserving key information:

{total_content}

Provide a concise summary that captures the main points and key details:"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback: truncate content if LLM call fails
            return total_content[:self.max_tokens * 4]  # Rough character limit
    
    async def answer_question(self, question: str, context_articles: List[Dict[str, Any]]) -> str:
        """Generate answer based on question and context articles"""
        if not context_articles:
            return "No relevant context found to answer your question."
        
        # Prepare context
        context_parts = []
        for article in context_articles:
            article_text = f"Title: {article.get('title', '')}\n"
            article_text += f"Author: {article.get('author_name', 'Unknown')}\n"
            article_text += f"Category: {article.get('category_name', 'Unknown')}\n"
            article_text += f"Content: {article.get('content', '')}\n"
            
            # Add tags if available
            if article.get('tags'):
                tags = [tag.get('name', '') for tag in article['tags']]
                article_text += f"Tags: {', '.join(tags)}\n"
            
            context_parts.append(article_text)
        
        # Combine all context
        full_context = "\n\n---\n\n".join(context_parts)
        
        # Check if context needs summarization
        if self.estimate_tokens(full_context) > self.max_tokens:
            full_context = await self.summarize_context(context_articles)
        
        # Create the prompt
        prompt = f"""Based on this context:

{full_context}

Question: {question}

Please provide a concise and accurate answer based on the information above. If the context doesn't contain enough information to answer the question, please say so."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    async def prioritize_articles(self, articles: List[Dict[str, Any]], question: str, max_articles: int = 5) -> List[Dict[str, Any]]:
        """Prioritize articles based on relevance to the question"""
        if len(articles) <= max_articles:
            return articles
        
        # Simple relevance scoring based on keyword matching
        question_words = set(re.findall(r'\b\w+\b', question.lower()))
        
        scored_articles = []
        for article in articles:
            score = 0
            title_words = set(re.findall(r'\b\w+\b', article.get('title', '').lower()))
            content_words = set(re.findall(r'\b\w+\b', article.get('content', '').lower()))
            
            # Score based on title matches (higher weight)
            title_matches = len(question_words.intersection(title_words))
            score += title_matches * 3
            
            # Score based on content matches
            content_matches = len(question_words.intersection(content_words))
            score += content_matches
            
            scored_articles.append((score, article))
        
        # Sort by score and return top articles
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for score, article in scored_articles[:max_articles]]


# Global LLM service instance
llm_service = LLMService()
