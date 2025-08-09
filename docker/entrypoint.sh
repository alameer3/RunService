#!/bin/bash
# Entry point script for VNC Desktop Docker container
# نقطة دخول container سطح مكتب VNC

set -e

# ألوان للإخراج
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting VNC Desktop Server Container${NC}"

# دالة انتظار الخدمات
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local timeout=${4:-30}
    
    echo -e "${YELLOW}⏳ Waiting for $service at $host:$port...${NC}"
    
    for i in $(seq 1 $timeout); do
        if nc -z $host $port >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service is ready${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}❌ $service not ready after $timeout seconds${NC}"
    return 1
}

# انتظار قاعدة البيانات
if [[ "${DATABASE_URL}" == *"postgres"* ]]; then
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    wait_for_service $DB_HOST 5432 "PostgreSQL" 60
fi

# انتظار Redis
if [[ "${REDIS_URL}" == *"redis"* ]]; then
    REDIS_HOST=$(echo $REDIS_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    wait_for_service $REDIS_HOST 6379 "Redis" 30
fi

# إعداد المتغيرات البيئية
export DISPLAY=${DISPLAY:-:1}
export PYTHONPATH="/app:$PYTHONPATH"

# إنشاء المجلدات المطلوبة
mkdir -p /app/logs
mkdir -p /app/data
mkdir -p /home/vncuser/.vnc

# إعداد VNC password
if [ ! -f /home/vncuser/.vnc/passwd ]; then
    echo -e "${YELLOW}🔑 Setting up VNC password...${NC}"
    echo "${VNC_PASSWORD:-vnc123456}" | x11vnc -storepasswd /home/vncuser/.vnc/passwd
fi

# تشغيل migrations قاعدة البيانات
echo -e "${YELLOW}🗄️ Running database migrations...${NC}"
cd /app
python3 -c "
from app import db, app
with app.app_context():
    try:
        db.create_all()
        print('✅ Database tables created successfully')
    except Exception as e:
        print(f'❌ Database error: {e}')
"

# اختيار نمط التشغيل
case "${1:-web}" in
    web)
        echo -e "${GREEN}🌐 Starting web server...${NC}"
        
        # بدء Xvfb في الخلفية
        echo -e "${YELLOW}📺 Starting virtual display...${NC}"
        Xvfb $DISPLAY -screen 0 1024x768x24 -ac +extension GLX +render -noreset &
        sleep 2
        
        # بدء openbox
        echo -e "${YELLOW}🪟 Starting window manager...${NC}"
        openbox &
        sleep 1
        
        # بدء VNC server في الخلفية
        echo -e "${YELLOW}🖥️ Starting VNC server...${NC}"
        x11vnc -display $DISPLAY -forever -usepw -shared -rfbauth /home/vncuser/.vnc/passwd -rfbport 5900 -bg -o /app/logs/vnc.log
        
        # بدء تطبيق الويب
        echo -e "${GREEN}🚀 Starting Flask application...${NC}"
        exec gunicorn --bind 0.0.0.0:5000 \
            --workers ${WORKERS:-2} \
            --worker-connections ${WORKER_CONNECTIONS:-1000} \
            --worker-class eventlet \
            --timeout 120 \
            --keepalive 5 \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            --access-logfile /app/logs/access.log \
            --error-logfile /app/logs/error.log \
            --log-level info \
            main:app
        ;;
        
    vnc)
        echo -e "${GREEN}🖥️ Starting VNC-only mode...${NC}"
        
        # بدء Xvfb
        Xvfb $DISPLAY -screen 0 1024x768x24 -ac +extension GLX +render -noreset &
        sleep 2
        
        # بدء openbox
        openbox &
        sleep 1
        
        # بدء Firefox في الخلفية
        firefox &
        
        # بدء VNC server (foreground)
        exec x11vnc -display $DISPLAY -forever -usepw -shared -rfbauth /home/vncuser/.vnc/passwd -rfbport 5900 -o /app/logs/vnc.log
        ;;
        
    celery)
        echo -e "${GREEN}⚙️ Starting Celery worker...${NC}"
        exec celery -A celery_worker.celery worker --loglevel=info --concurrency=2
        ;;
        
    shell)
        echo -e "${GREEN}🐚 Starting interactive shell...${NC}"
        exec /bin/bash
        ;;
        
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Available commands: web, vnc, celery, shell"
        exit 1
        ;;
esac