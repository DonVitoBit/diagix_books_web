#!/usr/bin/expect -f

set timeout 30

# Параметры подключения
set host "147.45.232.140"
set user "root"
set password "qQ6H^c7-et5J+S"

# Подключение к серверу
spawn ssh -o StrictHostKeyChecking=no $user@$host

# Ожидание запроса пароля
expect {
    "password:" {
        send "$password\r"
    }
    timeout {
        puts "Timeout waiting for password prompt"
        exit 1
    }
}

# Ожидание приглашения командной строки
expect "#"

# Проверка процесса streamlit
send "ps aux | grep streamlit | grep -v grep\r"
expect "#"

# Проверка статуса UFW
send "ufw status\r"
expect "#"

# Проверка открытых портов
send "netstat -tuln | grep 8501\r"
expect "#"

# Открытие порта 8501 в файрволле
send "ufw allow 8501/tcp\r"
expect "#"

# Проверка статуса UFW после изменений
send "ufw status\r"
expect "#"

# Проверка логов
send "tail -n 30 /var/log/streamlit.log\r"
expect "#"

puts "\n=== Deployment check completed ==="

# Интерактивная сессия
interact
