# pipenv gather image
FROM tiangolo/uwsgi-nginx:python3.8  as build-image

COPY Pipfile* /app/
WORKDIR /app

RUN pip3 install pipenv
RUN pipenv install --system --deploy --ignore-pipfile

# actual run image
FROM tiangolo/uwsgi-nginx:python3.8

RUN pip3 install flask SQLAlchemy bcrypt
COPY --from=build-image /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/

COPY anginx.conf /etc/nginx/conf.d/
COPY . /app
WORKDIR /app