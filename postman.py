# simple postfix manager

# zeved.ionut@gmail.com

# WORK IN PROGRESS

import subprocess
import sys
import re

postqueue_entries = []
mail_ids = []
mail_from = []
fail_reason = []
mail_to = []


def empty_lists():
  del postqueue_entries[:]
  del mail_ids[:]
  del mail_from[:]
  del fail_reason[:]
  del mail_to[:]


def process_queue():
  # in case this is not the first time we process the queue.
  empty_lists()

  postqueue_output = subprocess.check_output(['postqueue', '-p'])
  postqueue_output = postqueue_output.splitlines()
  # pop first and last element -> don't need them
  postqueue_output.pop(0)
  postqueue_output.pop(len(postqueue_output) - 1)

  # group them by 4 (each 4 lines = one queue entry)
  postqueue_entries = [postqueue_output[n:n + 4] for n in range(0, len(postqueue_output), 4)]

  for postqueue_entry in postqueue_entries:
    # get postqueue IDs
    mail_ids.append(postqueue_entry[0][0:12])
    # keep the index of the last mail ID appended.
    index = len(mail_ids) - 1
    # and FROM email addresses
    mf = re.search(r'[\w\.-]+@[\w\.-]+', postqueue_entry[0])
    if mf is None:
      # mailer daemon etc ???
      mail_from.append('(???)')
    else:
      mail_from.append(mf.group(0))

    # get fail mesage
    if postqueue_entry[1].find('Greylisted') != -1:
      fail_reason.insert(index, 'greylisted')
    elif postqueue_entry[1].find('not found') != -1:
      fail_reason.insert(index, 'host not found')
    elif postqueue_entry[1].find('refused') != -1:
      fail_reason.insert(index, 'connection err / host not found')
    elif postqueue_entry[1].find('No route') != -1:
      fail_reason.insert(index, 'no route to host (host error)')
    else:
      fail_reason.insert(index, 'unknown')

    # and finally get TO address
    mail_to.insert(index, postqueue_entry[2].strip())


def process_mail(mail_id):
  mail_cat = subprocess.check_output(['postcat', '-qbh', mail_id])
  mail_cat = mail_cat.splitlines()

  for line in mail_cat:
    if line.find('X-Spam-Flag: YES') != -1:
      return 'spam'


def exit():
  sys.exit()


def show_fullqueue():
  process_queue()

  greylisted_num = 0
  host_err_num = 0

  for mail_id in mail_ids:
    if fail_reason[mail_ids.index(mail_id)] == 'greylisted':
      greylisted_num += 1
    else:
      host_err_num += 1
    print('%s: %s >>> %s : reason: %s' %
      (mail_id,
       mail_from[mail_ids.index(mail_id)],
       mail_to[mail_ids.index(mail_id)],
       fail_reason[mail_ids.index(mail_id)])
    )

  print('\n%d messages waiting in the queue' % len(mail_ids))
  print('%d are greylisted (will retry sending)' % greylisted_num)
  print('%d are remote host problems (most likely will never be sent)' % host_err_num)


def show_greylisted_queue():
  process_queue()
  greylisted_num = 0

  for mail_id in mail_ids:
    if fail_reason[mail_ids.index(mail_id)] == 'greylisted':
      print('%s: %s >>> %s' %
         (mail_id,
          mail_from[mail_ids.index(mail_id)],
          mail_to[mail_ids.index(mail_id)])
      )
      greylisted_num += 1

  print('\n%s greylisted messages in the queue' % greylisted_num)


def show_host_error_queue():
  process_queue()
  host_err_num = 0

  for mail_id in mail_ids:
    if fail_reason[mail_ids.index(mail_id)].find('host') != -1:
      print('%s: %s >>> %s' %
         (mail_id,
          mail_from[mail_ids.index(mail_id)],
          mail_to[mail_ids.index(mail_id)])
      )
      host_err_num += 1

  print('\n%s host error messages in the queue' % host_err_num)


def show_spam_queue():
  process_queue()
  spam_num = 0

  for mail_id in mail_ids:
    if process_mail(mail_id) == 'spam':
      print('%s: %s >>> %s SPAM' % (mail_id, mail_from[mail_ids.index(mail_id)],
          mail_to[mail_ids.index(mail_id)]))
      spam_num += 1

  print('\n%s spam messages in the queue' % spam_num)


def delete_queue():
  show_fullqueue()

  print('\ntype 0 to return to main menu\n')
  mail_id = raw_input('message to delete > ')

  if len(mail_id) == 12:
    subprocess.call(['postsuper', '-d', mail_id])
    delete_queue()
  elif mail_id == '0':
    main_menu()
  else:
    print('\nmessage ID is not valid\n')
    delete_queue()


def postqueue_flush():
  subprocess.call(['postqueue', '-f'])
  main_menu()


options = {
  '0': exit,
  '1': show_fullqueue,
  '2': show_greylisted_queue,
  '3': show_host_error_queue,
  '4': show_spam_queue,
  '5': delete_queue,
  '6': postqueue_flush
}

selected = -1

def main_menu():
  print('\npostman 0.1\n')
  print('[1] show complete postfix queue')
  print('[2] show greylisted queue')
  print('[3] show host error emails queue')
  print('[4] show spam queue')
  print('[5] delete mail')
  print('[6] flush mail')
  print('[0] exit\n')

  selected = raw_input(' > ')
  print('\n')
  if selected in options.keys():
    subprocess.call('clear')
    options[selected]()

  main_menu()

main_menu()