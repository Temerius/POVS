для того чтобы избавиться от использования суперпользователя для пользовательских учеток создается роль 
dbowner
для нее прописываются права для каждой базы после создания:

GRANT ALL PRIVILEGES ON SCHEMA public to dbowner;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dbowner;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dbowner;

ALTER DEFAULT PRIVILEGES IN SCHEMA public FOR USER cicd GRANT ALL PRIVILEGES ON TABLES TO dbowner;
ALTER DEFAULT PRIVILEGES IN SCHEMA public FOR USER cicd GRANT ALL PRIVILEGES ON SEQUENCES TO dbowner;

в новой базе после ее создания овнером прописывается роль dbowner



если у пользователя должны быть права по максимуму то ему прописывается членство в dbowner:
GRANT dbowner TO %username% WITH INHERIT TRUE или GRANT dbowner TO %username%;
если нужен доступ только на чтение можно ипользовать встроенную роль pg_read_all_data


---------------------------------------------------
ЗАПУСК РОЛИ:

Копируем папку с ролью со своей локальной машины на джамп хост (msk-cicd102) и потом с него на msk-cicd101 или на ранчер (ansible@msk-rancher-001.das.digtp.com) (10.72.27.5)
в зависимости откуда есть сетевая связанность с целевыми машинами

Заходим по ssh на сервер с которого решили запускать (msk-cicd101 или ранчер)

Запуск роли на сервере:

export SPATH1="/home/ansible/pg/"   -определяем в переменной окружения путь до роли (в примере я использовал для роли директорию /home/ansible/pg/)


export SPATH2="/home/ansible/.ssh/"   -определяем в переменной окружения путь до ssh ключей


sudo docker run -ti -v ${SPATH1}:/app -v ${SPATH2}:/keys  repo.das.digtp.com:5000/base/ansible-alpine:32.0 /bin/sh   -запускаем контейнер с Ансибл

Внутри запущенного контейнера:

mkdir -p /root/.ssh/    -создаём директорию
cd /keys   -переходим в примонтированный вольюм с ключами
cp id_rsa.pub /root/.ssh -vvv   -копируем pub ключ
cp id_rsa /root/.ssh -vvv    -копируем priv ключ

ssh-copy-id -i /root/.ssh/id_rsa.pub 10.72.90.46   -копируем публичный ключ на целевую машину (здесь в примере это ДЕВ проекта проекта SYS_KNOWLEDGESPACE_EC, меняете IP на вашу целевую машину)

ssh 'root@msk-ksdb101.das.digtp.com'   -проверяем, что из контейнера на целевую машину работает ssh авторизация по ключу (после успешной авторизации само собой командой exit возвращаемся обратно в контейнер)

cd /app/   -переходим в дректорию с ролью

ansible all --list-hosts -i /app/SYS_KNOWLEDGESPACE_EC/dev/hosts   -выводим список хостов (в выводе должен быть список хостов из файла /app/SYS_KNOWLEDGESPACE_EC/dev/hosts (пример) в вашем случае путь к host отличен)

ansible all -m ping -i /app/SYS_KNOWLEDGESPACE_EC/dev/hosts   -пингуем хосты из списка (в выводе видим удачный pong от хостов из списка)

ansible-playbook /app/SYS_KNOWLEDGESPACE_EC/dev/setup_dev.yml  -i SYS_KNOWLEDGESPACE_EC/dev/hosts -b -vv   -запускаем роль (в примере указаны пути /app/SYS_KNOWLEDGESPACE_EC/dev/setup_dev.yml  -i SYS_KNOWLEDGESPACE_EC/dev/hosts в вашем случае это пути к вашим плэйбуку и hosts файлу)