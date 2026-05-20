import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .routes import scans
from .database import engine
from . import models

load_dotenv()

app = FastAPI(
    title='Argus-Sentinel API',
    description='Automated cybersecurity reconnaissance pipeline',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://frontend:5173', 'http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(scans.router, prefix='/api')


@app.get('/')
def root():
    return {
        'message': 'Argus-Sentinel API',
        'tagline': 'A hundred eyes on your attack surface.',
        'docs': '/docs',
        'version': '1.0.0',
    }


@app.get('/health')
def health_check():
    return {'status': 'ok'}
