import sys
import regex

def name(nametext):
#    if len(nametext) <= 64:
#        if nametext[0].isalpha():
#            if '' not in nametext.split('_'):
#                if regex.match('[\w]+$', nametext):
#                    return True
    if regex.match(r'[A-Za-z][\w]+$', nametext) and nametext.find('__') == -1:
        return True
def title(titletext):
    if len(titletext) <= 64:
        return True