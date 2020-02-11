ARG PYVER
FROM python:${PYVER}

ARG PACKAGES
ARG JOBNAME
ENV PACKAGES=${PACKAGES} JOBNAME=${JOBNAME}
COPY . /src/
RUN echo PACKAGES=${PACKAGES} JOBNAME=${JOBNAME} ; \
  pip install ${PACKAGES} && \
  apt update && \
  apt install -yq libglu1-mesa && \
  cd /src && \
  /src/.ci/run_tests.bash ${JOBNAME}
