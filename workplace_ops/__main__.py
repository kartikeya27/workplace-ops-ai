"""Run locally: python -m workplace_ops"""
import uvicorn

if __name__ == '__main__':
    uvicorn.run('workplace_ops.app:app', host='127.0.0.1', port=8000)
