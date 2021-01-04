# Build stage:
FROM python:3.8-slim-buster as build-image
COPY . /app
WORKDIR /app

#RUN apk add --no-cache --virtual build-deps gcc python3-dev musl-dev && \
#    apk add --no-cache postgresql-dev

RUN pip3 install pipenv
RUN pipenv install --system --deploy --ignore-pipfile

##########################################################################################

# "Default" stage:
FROM python:3.8-slim-buster

RUN pip3 install flask SQLAlchemy

# Copy generated site-packages from former stage:
COPY --from=build-image /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/

COPY . /app
WORKDIR /app

EXPOSE 5000

CMD flask run --host=0.0.0.0
