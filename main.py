import random
import math
import json
from optparse import OptionParser

class SportSlot():
    def __init__(self, name, max_student):
        self.name        = name
        self.max_student = max_student
        self.students    = []
        self.cost  = 0
    def show(self):
        print(self.name + "("+str(self.max_student)+")")

class SportSlotPool():
    def __init__(self):
        self.slotpool = []

    def generateFake(self, nb_slot, range_min_student=5, range_max_student=10):
        print("Generate fake sport slot pool")
        for i in range(nb_slot):
            self.slotpool.append(SportSlot("Sport " + str(i), random.randint(range_min_student,range_max_student)))

    def loadFromJSON(self, filename):
        with open(filename, 'r', encoding='utf-8') as outfile:
            print("Load Sport Slot from " + filename)
            data = json.load(outfile)
        for s in data["rows"]:
            self.slotpool.append(SportSlot(str(s["id"]), int(s["places_dispo"])))

    def getOptionsList(self):
        options = []
        for s in self.slotpool:
            options.append(s.name)
        return options

    def computeCostSorting(self, studentpool, alpha=1, show=False):

        # Compute cost of popularity
        total = 0
        for ids, sp in enumerate(self.slotpool):
            for s in studentpool.students:
                for idc, c in enumerate(s.choices):
                    if c == sp.name:
                        sp.cost += studentpool.nb_choices - idc
                        total += studentpool.nb_choices - idc

        # Compute number of student who can be allocated
        maxStudent = 0
        for sp in self.slotpool:
            maxStudent += sp.max_student

        # Compute general cost function
        for sp in self.slotpool:
            sp.cost = sp.cost / total + alpha * (sp.max_student/maxStudent)

        def sortcost(val):
            return val.cost

        self.slotpool.sort(key=sortcost, reverse = False)

        if show:
            for s in self.slotpool:
                print(str(s.cost) + " " + s.name + "("+str(s.max_student)+")")

    def allocateStudentIter(self,studentpool,  strength=2, ratio=1):

        for sp in self.slotpool:
            # Get list of students who select this sport slot at this round
            listStudent = studentpool.getStudentChoice(sp.name)

            # We allocate until there is no more student or we reach the max number of student for the slot
            while math.ceil(len(sp.students)*(1/ratio)) < sp.max_student and len(listStudent) > 0:
                # compute probalistic distribution
                # - The probability to be selected is reinforced by the round^strength of the student
                total = 0
                for s in listStudent:
                    total += pow(s.round,strength)

                for s in listStudent:
                    if math.ceil(len(sp.students)*(1/ratio)) >= sp.max_student:
                        break

                    # Build student preference probability to be selected
                    prob = pow(s.round,strength) / total
                    if random.random() < prob:
                        # Student selected
                        s.slot = sp.name
                        sp.students.append(s)
                        listStudent.remove(s)

            # We remove the preference for student who do not have been selected
            if len(sp.students) == sp.max_student:
                for s in listStudent:
                    s.choices[s.round-1] = None

    def allocateStudent(self,studentpool, iter=40, strength=2):
        for i in range(int(iter/2)):
            print("Allocate sub space " + str(i))
            self.allocateStudentIter(studentpool,strength=strength, ratio=(i+1)/(iter/2))
        for i in range(int(iter/2)):
            print("Allocate full space " + str(i))
            self.allocateStudentIter(studentpool,strength=strength)

    def stat(self, show_student=False):
        maxStudent = 0
        for sp in self.slotpool:
            print(sp.name+" ("+str(len(sp.students))+" / " +str(sp.max_student)+")")
            maxStudent += sp.max_student
            if show_student:
                for s in sp.students:
                    print(s.name + " (" + str(s.round)+")")
        print("Max student " + str(maxStudent))

    def show(self):
        for s in self.slotpool:
            s.show()
# =====================================
class Student():
    def __init__(self,name):
        self.name  = name
        self.round = 1
        self.choices = []
        self.slot = None

    def show(self):
        print(self.name)
        print(self.choices)

class StudentPool():
    def __init__(self, nb_choices=4):
        self.nb_choices = nb_choices
        self.students = []

    # Return the list of student who has slotname in next choice preference
    def getStudentChoice(self, slotname):
        listStudent = []
        for s in self.students:
            # If the student has already be allocated, we skip
            if s.slot is not None:
                continue

            # Select the first available preference
            for idx, c in enumerate(s.choices):
                if c is not None:
                    break
            # Store student preference round
            s.round = idx + 1

            # if the sport slot is the next preference of the student, he is candidate
            if c == slotname:
                listStudent.append(s)
        return listStudent

    def getStudent(self,name):
        for f in self.students:
            if f.name == name:
                return f
        return None

    def loadFromJSON(self, slotpool, filename):
        with open(filename, 'r', encoding='utf-8') as outfile:
            print("Load Student Choices from " + filename)
            data = json.load(outfile)

        for ds in data["rows"]:
            s = self.getStudent(ds["student_pk"])
            if s == None:
                s = Student(ds["student_pk"])
                s.choices = [-1] * self.nb_choices
                self.students.append(s)
            s.choices[ds["voeu"]-1] = str(ds["sport_pk"])

    def export(self, export_file):
        print("Export to " + export_file)
        result = []
        for s in self.students:
            result.append({
                    "student_pk" : s.name,
                    "sport_pk": s.slot
                    })

        with open(export_file, 'w', encoding='utf-8') as outfile:
            json.dump(result, outfile)

    def generateFake(self,slotpool,total=100):
        print("Generate fake student pool")
        options = slotpool.getOptionsList()
        for i in range(total):
            s = Student("Student " + str(i));
            s.choices = random.sample(options, k=self.nb_choices)
            self.students.append(s)

    def show(self):
        print("Number of students: " + str(len(self.students)))

    def stat(self):
        withoutAllocation = []
        ChoiceDistance = [0]*self.nb_choices
        for s in self.students:
            ChoiceDistance[s.round-1] += 1
            if s.slot == None:
                withoutAllocation.append(s)
        print("Number of students: " + str(len(self.students)))
        print("Student allocated : " + str(len(self.students)-len(withoutAllocation)))
        print("Student without allocation : " + str(len(withoutAllocation)))
        print(ChoiceDistance)


# =====================================
parser = OptionParser()
parser.add_option("", "--file-slot", dest="filename_slot",
                  help="list of available sport slot", metavar="FILE")

parser.add_option("", "--file-student", dest="filename_student",
                  help="list of student choices", metavar="FILE")

parser.add_option("", "--export", dest="export_file",
                  help="export file (json)", metavar="FILE")

parser.add_option("","--fake", action="store_true", dest="fake")

(options, args) = parser.parse_args()

slotpool = SportSlotPool()
if options.fake:
    slotpool.generateFake(150, range_min_student=10, range_max_student=35)
if options.filename_slot:
    slotpool.loadFromJSON(options.filename_slot)
slotpool.show()

studentpool = StudentPool(nb_choices=10)
if options.fake:
    studentpool.generateFake(slotpool, 3000)
if options.filename_student:
    studentpool.loadFromJSON(slotpool,options.filename_student)
studentpool.show()

# Sort sport slot allocation order according to invert popularity and number of available place
slotpool.computeCostSorting(studentpool, show=True)

print("Allocation\n=============")
slotpool.allocateStudent(studentpool, iter=100, strength=8)

print("Statistics\n=============")
slotpool.stat()
studentpool.stat()

if options.export_file:
    studentpool.export(options.export_file)
