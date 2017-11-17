#!/usr/bin/env python
# encoding: utf-8

trans_dict_lookup = {
    'direct': 'regular payments',
    'faster': 'regular payments',
    'card': 'expenditure',
    'standing': 'regular payments',
    'interest': 'fees',
    'transfer': 'inter account transfers',
    'bank': 'pay',
    'cheque': 'expenditure',
    'payment': 'expenditure',
    'daily': 'fees',
    'bill': 'regular payments',
    'cash': 'cash',
    'overseas': 'fees',
    'to': 'inter account transfers',
    'from': 'inter account transfers',
    'b-paymnt': 'inter account transfers',
    'net': 'ignore',
    'failed': 'failed payments',
    'link': 'ignore',
    'arranged': 'fees',
    'paid': 'expenditure',
    'unarranged': 'fees',
    'credit': 'payment received',
    'non-sterling': 'fees',
    'withdrawal': 'cash',
    'post': 'cash',
    'correction': 'ignore'
}