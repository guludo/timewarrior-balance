import collections
import datetime
import json
import operator
import pathlib
import sys
import re


# These objects are used as special keys for deltas:
# - UNTAGGED: For deltas that do not have associated tags
# - TOTAL: To aggregate all deltas
UNTAGGED = object()
TOTAL = object()


def main():
    # Get input information for the report
    timew = read_timew_input()

    # Read our own configuration file
    conf_path = pathlib.Path(timew['conf']['temp.db']) / 'balance.conf'
    bal_conf = ConfParser(conf_path, timew).parse()

    # Calculate deltas
    deltas = collections.defaultdict(datetime.timedelta)
    for entry in timew['entries']:
        dt = entry['end'] - entry['start']
        deltas[TOTAL] += dt
        for tag in entry.get('tags', [UNTAGGED]):
            deltas[tag] += dt

    # Calculate owing deltas
    owing = collections.defaultdict(datetime.timedelta)
    for tag, conf_block in bal_conf.items():
        # Calculate by periods
        for period in conf_block['periods']:
            # Get intersection
            per_start, per_end = period['start'], period['end']
            inter_start = max(per_start, timew['report_start'])
            inter_end = min(per_end, timew['report_end'])
            if inter_start > inter_end:
                # Intersection is empty
                continue
            # Get interval in local timezone in order to get the weekdays
            inter_start = inter_start.astimezone()
            inter_end = inter_end.astimezone()
            # Adjust inter_start so that it is exactly at midnight
            inter_start = inter_start.replace(hour=0,
                                              minute=0,
                                              second=0,
                                              microsecond=0)
            # Get how many occurrences of each weekday and multiply by deltas
            for days in range(7):
                d = inter_start + datetime.timedelta(days=days)
                if d >= inter_end:
                    break
                # Number of occurrences is the ceil division by of number of
                # days by 7, that is, the number of weeks found
                num_occurrences = ((inter_end - d).days + 6) // 7
                weekday = d.weekday()
                delta = num_occurrences * period['weekday_deltas'][weekday]
                owing[tag] += delta
                owing[TOTAL] += delta

        # Calculate by entry dates
        for date_entry in conf_block['date_entries']:
            if (timew['report_start'] <= date_entry['date']
                    and date_entry['date'] < timew['report_end']):
                owing[tag] += date_entry['delta']
                owing[TOTAL] += date_entry['delta']


    header = ('Tag', 'Spent', 'Allotted', 'Balance')
    rows = []
    untagged_row = None
    total_row = None

    tags = set(deltas) | set(owing)
    for tag in tags:
        paid_minutes = round(deltas[tag].total_seconds() / 60)
        owing_minutes = round(owing[tag].total_seconds() / 60)
        balance_minutes = paid_minutes - owing_minutes
        if tag is TOTAL:
            total_row = (
                'TOTAL',
                to_hour_format(paid_minutes),
                to_hour_format(owing_minutes),
                to_hour_format(balance_minutes, True),
            )
        elif tag is UNTAGGED:
            if paid_minutes or owing_minutes:
                untagged_row = (
                    '<untagged>',
                    to_hour_format(paid_minutes),
                    to_hour_format(owing_minutes),
                    to_hour_format(balance_minutes, True),
                )
        else:
            rows.append((
                tag,
                to_hour_format(paid_minutes),
                to_hour_format(owing_minutes),
                to_hour_format(balance_minutes, True),
            ))

    rows.sort(key=operator.itemgetter(0))
    if untagged_row:
        rows.append(untagged_row)

    widths = tuple(
        max(len(header[i]), len(total_row[i]), *(len(r[i]) for r in rows))
        for i in range(len(header))
    )

    print(f'Start: {timew["report_start"].astimezone().ctime()}')
    print(f'  End: {timew["report_end"].astimezone().ctime()}')
    print()

    # Print header
    gap = 2
    line = (' ' * gap).join(
        f'{{:>{w}s}}'.format(name) for name, w in zip(header, widths)
    )
    print(line)
    line = ('─' * gap).join('─' * w for w in widths)
    print(line)

    # Print rows
    for row in rows:
        line = (' ' * gap).join(
            f'{{:>{w}s}}'.format(v) for v, w in zip(row, widths)
        )
        print(line)

    # Print total
    line = ('─' * gap).join('─' * w for w in widths)
    print(line)
    line = (' ' * gap).join(
        f'{{:>{w}s}}'.format(v) for v, w in zip(total_row, widths)
    )
    print(line)


datetime_re = re.compile(r'^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$')
def parse_datetime(s, value_desc):
    m = datetime_re.match(s)
    if not m:
        raise RuntimeError(f'unable to parse {value_desc}: {s}')
    return datetime.datetime(
        int(m.group(1)),
        int(m.group(2)),
        int(m.group(3)),
        int(m.group(4)),
        int(m.group(5)),
        int(m.group(6)),
        tzinfo=datetime.timezone.utc,
    )


def to_hour_format(minutes, explicity_sign=False):
    h, m = minutes // 60, abs(minutes) % 60
    if explicity_sign:
        h = f'{h:+}'
    return f'{h}:{m:02d}'


class ConfParser:
    whitespace_re = re.compile(r'\s+')
    comment_re = re.compile(r'#.*(\n|$)')

    token_confs = [
        '__untagged__',
        'from',
        'to',
        '{',
        '}',
        {
            'name': '<end-of-time>',
            'pattern': re.compile(r'end\s+of\s+time'),
        },
        {
            'name': '<date>',
            'pattern': re.compile(r'\d{4}-\d{2}-\d{2}'),
        },
        {
            'name': '<weekday>',
            'pattern': re.compile(r'sun|mon|tue|wed|thu|fri|sat'),
        },
        {
            'name': '<hours>',
            'pattern': re.compile(r'(-|\+?)[0-9]+(:[0-5][0-9])?'),
        },
        {
            'name': '<str>',
            'pattern': re.compile(r'"(\\"|[^"])+"'),
        },
        {
            'name': '<word>',
            'pattern': re.compile(r'\w+'),
        },
    ]

    def __init__(self, path, timew):
        self.path = path
        self.default_end = timew['report_end']
        try:
            self.confstr = path.read_text()
        except FileNotFoundError:
            print(f'missing configuration file {path}', file=sys.stderr)
            exit(1)

        self.next_head = 0
        self.next_lineno = 1

        self.cur_head = 0
        self.cur_lineno = -1
        self.cur_token = None

    def parse(self):
        self.read_token()
        conf = {}
        while self.cur_token in ('<str>', '<word>', '__untagged__'):
            tag, block_conf = self.parse_tag_block()
            if tag in conf:
                self.error(f'more than two blocks found for tag {tag!r}')
            conf[tag] = block_conf
        self.match('<end-of-file>')
        return conf

    def parse_block(self):
        periods = []
        date_entries = []
        while True:
            if self.cur_token == 'from':
                periods.append(self.parse_period())
            elif self.cur_token == '<date>':
                date_entries.append(self.parse_date_entry())
            else:
                break

        for i in range(len(periods) - 1):
            if periods[i]['end'] is None:
                periods[i]['end'] = periods[i + 1]['start']

        for p in periods:
            if p['end'] == 'end-of-time' or p['end'] is None:
                p['end'] = self.default_end

        return {'periods': periods, 'date_entries': date_entries}

    def parse_date_entry(self):
        date = self.match('<date>')
        delta = self.match('<hours>')

        note = ""
        if self.cur_token == '<str>':
            note = self.match('<str>')

        return {'date': date, 'delta': delta, 'note': note}

    def parse_period(self):
        self.match('from')
        start = self.match('<date>')
        if self.cur_token == 'to':
            self.match('to')
            if self.cur_token == '<end-of-time>':
                end = self.match('<end-of-time>')
            else:
                end = self.match('<date>')
        else:
            end = None

        weekday_deltas = [datetime.timedelta() for weekday in range(7)]
        self.match('{')
        while self.cur_token == '<weekday>':
            weekday = self.match('<weekday>')
            weekday_deltas[weekday] += self.match('<hours>')
        self.match('}')

        return {'start': start, 'end': end, 'weekday_deltas': weekday_deltas}

    def parse_tag_block(self):
        if self.cur_token in ('<word>', '__untagged__'):
            tag = self.match(self.cur_token)
        else:
            tag = self.match('<str>')
            tag = tag[1:-1]
        self.match('{')
        block_conf = self.parse_block()
        self.match('}')
        return tag, block_conf

    def read_token(self):
        self.cur_head = self.next_head
        self.cur_lineno = self.next_lineno

        if self.cur_head >= len(self.confstr):
            self.cur_token = '<end-of-file>'
            return

        # Ignore blank space and comment
        while True:
            m = self.whitespace_re.match(self.confstr, self.cur_head)
            if not m:
                m = self.comment_re.match(self.confstr, self.cur_head)

            if m:
                self.cur_lineno += m.group(0).count('\n')
                self.cur_head = m.end()
            else:
                break

        if self.cur_head >= len(self.confstr):
            self.cur_token = '<end-of-file>'
            return

        # Find token
        for tk_conf in self.token_confs:
            if isinstance(tk_conf, str):
                if self.confstr.startswith(tk_conf, self.cur_head):
                    self.cur_token = tk_conf
                    self.cur_lexeme = tk_conf
                    break
            else:
                m = tk_conf['pattern'].match(self.confstr, self.cur_head)
                if m is not None:
                    self.cur_token = tk_conf['name']
                    self.cur_lexeme = m[0]
                    break
        else:
            self.error(f'unrecognized token type')
        self.next_head = self.cur_head + len(self.cur_lexeme)
        self.next_lineno = self.cur_lineno + self.cur_lexeme.count('\n')

    def match(self, expected):
        if self.cur_token != expected:
            self.error(f'expected {expected}, but found {self.cur_token}')

        lex = self.cur_lexeme
        self.read_token()

        if expected == '<hours>':
            hours_is_neg = lex.startswith('-')
            if lex.startswith('+') or lex.startswith('-'):
                lex = lex[1:]
            if ':' not in lex:
                lex += ':00'
            h, m = lex.split(':')
            h, m = int(h), int(m)
            delta = datetime.timedelta(hours=h, minutes=m)
            if hours_is_neg:
                delta = -delta
            return delta
        elif expected == '<date>':
            d = datetime.datetime(*(int(v) for v in lex.split('-')))
            d = d.astimezone(datetime.timezone.utc)
            return d
        elif expected == '<end-of-time>':
            return 'end-of-time'
        elif expected == '<str>':
            return lex[1:-1]
        elif expected == '<weekday>':
            return ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].index(lex)
        elif expected == '__untagged__':
            return UNTAGGED
        else:
            return lex

    def error(self, msg):
        frag_end = self.confstr.find('\n', self.cur_head)
        frag = self.confstr[self.cur_head:frag_end]
        msg = f'{self.path}:{self.cur_lineno}: {msg}: {frag}'
        print(msg, file=sys.stderr)
        exit(1)


def read_timew_input():
    name_value_re = re.compile(r'^(.+): (.*)\n$')

    # Read configuration
    # ------------------
    conf = {}
    while True:
        line = sys.stdin.readline()
        m = name_value_re.match(line)
        if not m:
            break
        conf[m.group(1)] = m.group(2)

    # Read entries
    # ------------
    entries = json.loads(line + sys.stdin.read())

    # Generate report_start and report_end
    # ------------------------------------
    start_input = conf['temp.report.start']
    end_input = conf['temp.report.end']

    if start_input:
        report_start = parse_datetime(start_input, 'report start time')
    else:
        # Add one day to the minimal date in order to allow conversion from and
        # to UTC without overflow errors.
        report_start = datetime.datetime.min + datetime.timedelta(days=1)
        report_start = report_start.astimezone(datetime.timezone.utc)

    if end_input:
        report_end = parse_datetime(end_input, 'report end time')
    else:
        report_end = datetime.datetime.now(datetime.timezone.utc)

    # Normalize values of entries
    # ---------------------------
    default_entry_end = datetime.datetime.now(datetime.timezone.utc)
    for entry in entries:
        entry['start'] = parse_datetime(entry['start'],
                                        f'start time for @{entry["id"]}')
        if 'end' in entry:
            entry['end'] = parse_datetime(entry['end'],
                                          f'start time for @{entry["id"]}')
        else:
            entry['end'] = default_entry_end

    return {
        'conf': conf,
        'entries': entries,
        'report_start': report_start,
        'report_end': report_end,
    }


if __name__ == '__main__':
    main()
