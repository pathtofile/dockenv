FROM python:3
WORKDIR /usr/src/app
COPY . .
RUN python build.py
RUN rm build.py
CMD [ "sh", "./runner/run.sh" ]
