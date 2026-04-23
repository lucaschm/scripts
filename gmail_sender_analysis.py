import mailbox
import email.utils
from collections import Counter
import csv

# Path to your MBOX file
mbox_path = input("mbox path: ")

# csv output file
output_file = input("csv output file: ")

# Load mailbox
mbox = mailbox.mbox(mbox_path)

senders = Counter()

for message in mbox:
    if message['from']:
        name, addr = email.utils.parseaddr(message['from'])
        if addr:
            senders[addr.lower()] += 1

# Sort by count (descending)
sorted_senders = senders.most_common()

# Save to CSV
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Email Address", "Number of Emails"])
    writer.writerows(sorted_senders)

# Print top 20
print("Top 20 senders:")
for email_addr, count in sorted_senders[:20]:
    print(f"{email_addr}: {count}")