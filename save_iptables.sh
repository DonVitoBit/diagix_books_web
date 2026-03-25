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

# Установка iptables-persistent для сохранения правил
send "apt install -y iptables-persistent\r"

# Ждем завершения установки (может потребоваться подтверждение)
expect {
    "Save current IPv4 rules?" {
        send "y\r"
        exp_continue
    }
    "Save current IPv6 rules?" {
        send "y\r"
        exp_continue
    }
    "#" {
        puts "iptables-persistent installed"
    }
    timeout {
        puts "Installation timeout"
    }
}

# Сохранение текущих правил
send "iptables-save > /etc/iptables/rules.v4\r"
expect "#"

# Проверка сохраненных правил
send "cat /etc/iptables/rules.v4 | grep 8501\r"
expect "#"

puts "\n=== iptables rules saved successfully ==="

# Интерактивная сессия
interact
