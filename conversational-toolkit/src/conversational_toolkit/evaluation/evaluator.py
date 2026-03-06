"""
Batch evaluator and sample builders for the evaluation module.

'Evaluator' runs a list of 'Metric' objects concurrently over a batch of 'EvaluationSample' objects and returns an 'EvaluationReport'. All metrics are dispatched with 'asyncio.gather' so retrieval metrics (pure arithmetic) and generation metrics (LLM calls) run in parallel.

The two static factory methods cover the main usage patterns:
    'build_samples_from_agent': runs the full RAG pipeline for each query and wraps the answer and retrieved sources into 'EvaluationSample' objects.
    'build_samples_from_retriever': runs only the retrieval stage, useful for diagnosing retrieval quality independently of generation.
"""

import asyncio
from typing import Any, Sequence, cast

from conversational_toolkit.agents.base import Agent, QueryWithContext
from conversational_toolkit.evaluation.data_models import EvaluationReport, EvaluationSample, MetricResult
from conversational_toolkit.evaluation.metrics.base import Metric
from conversational_toolkit.llms.base import LLMMessage
from conversational_toolkit.retriever.base import Retriever
from conversational_toolkit.vectorstores.base import ChunkRecord


class Evaluator:
    """
    Batch runner that evaluates a list of metrics over a set of samples.

    Metrics are run concurrently. Within each metric, samples are processed sequentially to avoid overwhelming a rate-limited judge LLM.

    Attributes:
        metrics: The list of 'Metric' objects to evaluate.
    """

    def __init__(self, metrics: list[Metric]) -> None:
        self.metrics = metrics

    async def evaluate(
        self,
        samples: Sequence[EvaluationSample],
        metadata: dict[str, Any] | None = None,
    ) -> EvaluationReport:
        """Run all metrics concurrently over 'samples' and return an 'EvaluationReport'."""
        results: list[MetricResult] = list(await asyncio.gather(*(m.compute(samples) for m in self.metrics)))
        return EvaluationReport(
            results=results,
            num_samples=len(samples),
            metadata=metadata or {},
        )

    @staticmethod
    async def build_samples_from_agent(
        agent: Agent,
        queries: list[str],
        relevant_chunk_ids: list[set[str]] | None = None,
        ground_truth_answers: list[str | None] | None = None,
        history: list[LLMMessage] | None = None,
    ) -> list[EvaluationSample]:
        """Call the agent for each query and wrap the results into 'EvaluationSample' objects.

        This is the online diagnostic mode: it exercises the full pipeline from query to answer so both retrieval and generation quality can be measured on live traffic or a curated test set.

        Args:
            agent: The agent to evaluate.
            queries: One query per sample.
            relevant_chunk_ids: Optional list of ground-truth relevant chunk ID sets (one per query). Required for retrieval metrics.
            ground_truth_answers: Optional list of reference answers (one per query). Required for RAGAS AnswerCorrectness.
            history: Shared conversation history prepended to every query. Defaults to an empty history.

        Returns:
            One 'EvaluationSample' per query.
        """
        history = history or []
        samples: list[EvaluationSample] = []
        for i, query in enumerate(queries):
            answer = await agent.answer(QueryWithContext(query=query, history=history))
            samples.append(
                EvaluationSample(
                    query=query,
                    answer=answer.content[0].text,
                    retrieved_chunks=cast(list[ChunkRecord], list(answer.sources)),
                    history=list(history),
                    relevant_chunk_ids=relevant_chunk_ids[i] if relevant_chunk_ids else set(),
                    ground_truth_answer=ground_truth_answers[i] if ground_truth_answers else None,
                )
            )
        return samples

    @staticmethod
    async def build_samples_from_retriever(
        retriever: Retriever[ChunkRecord],
        queries: list[str],
        relevant_chunk_ids: list[set[str]] | None = None,
    ) -> list[EvaluationSample]:
        """Call the retriever for each query and wrap the results into 'EvaluationSample' objects.

        This is the retrieval-only mode: it isolates retrieval quality from generation so failing retrieval metrics can be diagnosed without running the LLM.

        Args:
            retriever: The retriever to evaluate. Accepts any 'Retriever[ChunkRecord]' subtype, including 'BM25Retriever', 'HybridRetriever', etc.
            queries: One query per sample.
            relevant_chunk_ids: Optional list of ground-truth relevant chunk ID sets (one per query). Required for retrieval metrics.

        Returns:
            One 'EvaluationSample' per query with an empty 'answer' field.
        """
        samples: list[EvaluationSample] = []
        for i, query in enumerate(queries):
            chunks = await retriever.retrieve(query)
            samples.append(
                EvaluationSample(
                    query=query,
                    answer="",
                    retrieved_chunks=list(chunks),
                    relevant_chunk_ids=relevant_chunk_ids[i] if relevant_chunk_ids else set(),
                )
            )
        return samples
