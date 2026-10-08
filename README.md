# 🌍 AI Travel Guide

An AI-powered travel guide that provides historical and cultural information about destinations and converts the generated guide into natural-sounding audio.

## ✨ Features

- 🔎 Destination exploration
- 🤖 AI-generated historical information
- 🌐 Multi-language support
- 🎙️ Male and female voice selection
- 🔊 AI-powered audio guide generation
- 🗣️ Murf Falcon text-to-speech
- 📱 Responsive web interface
- 🔐 Environment-based API key management

## 🏗️ Architecture

```text
User
 ↓
Frontend
 ↓
Flask REST API
 ├── Google Gemini
 │     ↓
 │   Travel description
 │
 └── Murf Falcon
       ↓
     MP3 Audio
       ↓
     Base64
       ↓
Frontend Audio Player