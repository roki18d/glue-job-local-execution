FROM amazon/aws-glue-libs:glue_libs_1.0.0_image_01

RUN pip install -U pip
RUN pip install jupyterlab
