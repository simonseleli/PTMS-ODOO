FROM odoo:13.0

USER root

COPY ./enterprise-addons /mnt/enterprise-addons
COPY ./custom-addons /mnt/custom-addons

COPY requirements.txt .

RUN pip install -r requirements.txt

USER odoo