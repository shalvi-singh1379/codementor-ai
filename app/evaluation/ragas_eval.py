import os
from dotenv import load_dotenv
from app.rag.retriever import retrieve
from app.rag.rag_pipeline import rag_query
from app.evaluation.test_questions import TEST_QUESTIONS


load_dotenv()

def build_evaluation_dataset() -> list[dict]:
    dataset = []

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/{len(TEST_QUESTIONS)}] processing: {question[:60]}...")

        # use rewritten query for retrieval if input looks like code
        from app.rag.rag_pipeline import rewrite_query_for_retrieval
        retrieval_query = rewrite_query_for_retrieval(question)

        retrieved_chunks = retrieve(retrieval_query, k=5)
        contexts = [chunk["text"] for chunk in retrieved_chunks]

        answer = rag_query(question)

        dataset.append({
            "question": question,
            "contexts": contexts,
            "answer": answer,
        })

    return dataset


def run_ragas_evaluation(dataset: list[dict]):
    """
    scores the dataset using RAGAS metrics, with Groq as the judge LLM.
    """
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy
    from langchain_groq import ChatGroq
    from langchain_community.embeddings import HuggingFaceEmbeddings

    judge_llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    judge_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    answer_relevancy.strictness = 1
    ragas_dataset = Dataset.from_list(dataset)

    print("\nrunning RAGAS evaluation (this calls the judge LLM multiple times per example)...\n")

    results = evaluate(
        ragas_dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=judge_llm,
        embeddings=judge_embeddings,
    )

    return results


if __name__ == "__main__":
    print("building evaluation dataset...\n")
    dataset = build_evaluation_dataset()
    print(f"\ndone! collected {len(dataset)} examples\n")

    print("\n=== INSPECTING DATASET BEFORE SCORING ===")
    for i, entry in enumerate(dataset, 1):
        print(f"\n--- Example {i} ---")
        print(f"Question: {entry['question'][:100]}")
        print(f"Answer (first 300 chars): {entry['answer'][:300]}")
        print(f"Num contexts: {len(entry['contexts'])}")
        print(f"First context (first 200 chars): {entry['contexts'][0][:200]}")
    results = run_ragas_evaluation(dataset)

    print("\n=== RAGAS EVALUATION RESULTS ===")
    print(results)