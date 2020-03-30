from datetime import time
from models import Medication

medicationsList = [
    Medication('Vitamin E (Alpha Tocopheryl Acetate)', [8]),
    Medication('Abidec/Dalivit', [8]),
    Medication('Vitamin K', [8]),
    Medication('Ranitidine', [8, 14, 22]),
    Medication('Cefalexin',[9, 22], 'Cefalexin is an antibiotic that should be given for & month after Kasai procedure.'),
    Medication('Prednisolone', [9], 'Prednisolone should be given after/with milk. No Immunisation should be given until one month after Prednisolone is stopped.'),
    Medication('Ursodeoxycholic Acid', [9, 21]),
    Medication('Phenobarbitone', [22], 'Phenobarbitone dose will be increased by 15mg each week up to a maximum dose of 45mg once a day as long as child is not too drowsy.')
]

def generate_chart(medications):
    hours = set([hour for med in medications for hour in med.time])
    for h in hours:
        meds = [med for med in medications if h in med.time]
        yield ','.join([time(hour=h).strftime("%I%p"), meds[0].name]) + '\n'
        # if there is more than one drug for this hour.
        for i in range(1, len(meds)):
            yield ','.join(["", meds[i].name]) + '\n'