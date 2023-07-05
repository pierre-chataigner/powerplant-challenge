FROM python:3.9
WORKDIR /
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt
COPY ./main.py /main.py
COPY ./solver.py /solver.py
CMD ["flask", "--app", "main", "run", "-p", "8888", "--host=0.0.0.0"]

