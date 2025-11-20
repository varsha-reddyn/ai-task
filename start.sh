#!/bin/bash

(cd backend && python main.py) &
BACKEND_PID=$!

(cd frontend && npm run dev) &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID
