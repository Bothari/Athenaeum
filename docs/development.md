# Development

## Building from Source

```bash
git clone https://github.com/Bothari/Athenaeum.git
cd Athenaeum
docker compose up -d --build
```

## Running Tests

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```
