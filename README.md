# Git-RAG

Git-RAG is a Retrieval-Augmented Generation (RAG) implementation that transforms a GitHub repository into a queryable knowledge base.

## Project Description

This project demonstrates a RAG-based system that enables users to interact with GitHub repositories through natural language queries. It utilizes **LightRAG** ([paper](https://arxiv.org/abs/2410.05779), [repository](https://github.com/HKUDS/LightRAG/tree/main)) to generate a knowledge graph from the codebase, and uses **Ollama** as the LLM backend.

The application is built with **FastAPI** and is fully dockerized. It exposes REST API endpoints that allow users to:

- Pull GitHub repositories, then ingest and process them to build a knowledge base,  
- Query the repositories using natural language through the generated knowledge base.

## Prerequisites

Before setting up the project, ensure you have the following installed:

- [Docker](https://www.docker.com/)  

## Setup

Clone this repository 
`git clone`