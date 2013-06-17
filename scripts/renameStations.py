import re

#nameMap = { 'ArlingtonCemetery' : 'ArlingtonCem', 'FoggyBottom' : 'FoggyBtm' }
           
# Generate the short name for a station,
# given the long name s
# Example: Columbia Heights -> ColumbiaHts
def shortName(s):
    s = re.sub(' ', '', s)
    s = re.sub('-', '', s)
    s = re.sub('\'', '', s)
    s = re.sub('Avenue','Ave',s)
#    s = re.sub('Center', 'Cntr',s)
    #s = re.sub('Square', 'Sq', s)
    #s = re.sub('Heights', 'Hts', s)
    #s = re.sub('Height','Hts', s) # For "Congress Height"
    #s = re.sub('Road', 'Rd', s)
    #s = re.sub('Place', 'Pl', s)
    #s = re.sub('Cemetery', 'Cem', s)
    #s = re.sub('Bottom', 'Btm', s)
    return s


    
