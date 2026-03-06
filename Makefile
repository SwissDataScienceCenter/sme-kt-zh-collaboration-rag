include .env.local
export

run:
	BACKEND=openai python -m sme_kt_zh_collaboration_rag.main
