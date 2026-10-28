# -*- coding: utf-8 -*-
"""Modulli to'lov provayderlari.

Hozir amalda bitta provayder bor: 'generic' - imzolangan (HMAC-SHA256) webhook. U sizning
to'lov tizimingiz (yoki oraliq server) to'lov tasdiqlanganda yuboradigan JSON:
    POST /payments/callback/generic
    Header:  X-Signature: hex(HMAC_SHA256(PAYMENT_CALLBACK_SECRET, request_body))
    Body:    {"reference": "TK-AB12CD", "amount": 10000, "txn_id": "provayderdagi-noyob-id"}
Click / Payme / Uzum kabi aniq provayderlar uchun ularning rasmiy hujjatiga mos yangi sinf
qo'shish kerak (merchant hisobi va kalitlar talab qilinadi) - hozircha IMPLEMENTATSIYA QILINMAGAN."""
import hashlib
import hmac
import json

from config import cfg


class Provider:
    name = ""

    def configured(self):
        return False

    def verify(self, headers, body):
        return False

    def parse(self, body):
        raise NotImplementedError


class GenericHMAC(Provider):
    name = "generic"

    def configured(self):
        return bool(cfg.payment_secret)

    def verify(self, headers, body):
        sig = headers.get("X-Signature", "")
        good = hmac.new(cfg.payment_secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig.lower(), good)

    def parse(self, body):
        d = json.loads(body.decode("utf-8"))
        return str(d.get("reference", "")), d.get("amount"), str(d.get("txn_id", ""))


PROVIDERS = {"generic": GenericHMAC()}
