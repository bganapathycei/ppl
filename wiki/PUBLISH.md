# Publish wiki to GitHub

The wiki content lives in this directory. Push it to the GitHub wiki git repository.

## Prerequisites

1. Enable **Wiki** on the repo: GitHub → **Settings** → **Features** → **Wikis** ✓
2. Git credentials with push access to `bganapathycei/ppl`

## One-time publish

From the repository root:

```bash
cd wiki
git init
git add .
git commit -m "Initial PPL wiki"
git branch -M main
git remote add origin https://github.com/bganapathycei/ppl.wiki.git
git push -u origin main
```

If GitHub expects `master` instead of `main`:

```bash
git branch -M master
git push -u origin master
```

## Update after edits

```bash
cd wiki
git add .
git commit -m "Update wiki"
git push
```

## Wiki URL

After the first push: **https://github.com/bganapathycei/ppl/wiki**

## Pages

| File | Wiki page |
|---|---|
| `Home.md` | Home |
| `Getting-Started.md` | Getting Started |
| `Visual-Editor.md` | Visual Editor |
| `Architecture.md` | Architecture |
| `Language-Reference.md` | Language Reference |
| `CLI-Reference.md` | CLI Reference |
| `Examples.md` | Examples |
| `Runtime-and-Execution-Graph.md` | Runtime and Execution Graph |
| `Providers-and-LLM-Configuration.md` | Providers and LLM Configuration |
| `Knowledge-Memory-and-Tools.md` | Knowledge Memory and Tools |
| `Governance-and-Human-Approval.md` | Governance and Human Approval |
| `Repository-Structure.md` | Repository Structure |
| `Release-History.md` | Release History |
