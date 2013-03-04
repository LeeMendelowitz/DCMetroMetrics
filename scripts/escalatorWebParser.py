# Lee Mendelowitz
# 2/19/2013
#
# Parse the data from the Metro escalator webpage
from HTMLParser import HTMLParser

def getDataLines(src):
    collect = False
    lines = (l.strip() for l in src.split('\n'))
    myLines = []
    for l in lines:
        if (l == '<!-- content -->'):
            collect = True
        if (l == '<!-- end content -->'):
            collect = False
            break;
        if collect:
            myLines.append(l)
    return myLines

class ElevatorTableParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        # We expect only to parse HTML tables with simple content (no embedded tables).
        # trDepth should be 0 or 1, tdDepth should be 0 or 1
        self.reset()

    def reset(self):
        HTMLParser.reset(self)
        self.trDepth = 0
        self.tdDepth = 0
        self.curRow = []
        self.rows = []

    def checkDepth(self, val):
        isOkay = val in (0,1)
        if not isOkay:
            raise Exception('ElevatorTableParser received malformed table!')

    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.tdDepth += 1
            self.checkDepth(self.tdDepth)
        elif tag == 'tr':
            self.trDepth += 1
            self.checkDepth(self.trDepth)

    def handle_endtag(self, tag):
        if tag == 'td':
            self.tdDepth -= 1
            self.checkDepth(self.tdDepth)
        elif tag == 'tr':
            self.trDepth -= 1
            self.checkDepth(self.trDepth)
            # store the data for this row
            if self.curRow:
                self.rows.append(tuple(self.curRow))
                self.curRow = []

    def handle_data(self, data):
        if self.trDepth == 1:
            data = data.strip()
            if data:
                self.curRow.append(data)

    def getRowData(self):
        return self.rows

def parseElevatorWebStatus(src):
    srcLines = getDataLines(src)
    src = '\n'.join(srcLines)
    parser = ElevatorTableParser()
    parser.feed(src)

    # Data is a list of tuples of form:
    # (Station, Unit description, Status, Est. Return Date)
    data = [d for d in parser.getRowData() if len(d)==4]
    data = data[1:] # Remove the table header

    def tupleToRecord(t):
        station = t[0]
        unitType, unitDesc = tuple(f.strip() for f in t[1].split('/', 1))
        status = t[2]
        estimate = t[3]
        rec = {'station': station,
               'unitType': unitType,
               'unitDesc': unitDesc,
               'status': status,
               'estimate':estimate}
        return rec
    data = [tupleToRecord(d) for d in data]
    return data
