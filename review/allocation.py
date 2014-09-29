import random

"""
Note: we could just match student numbers with student numbers for
this algorithm (ie. use 2 lists of student nbrs) 
based on the mapping between marking each other we can transfer
the assignment objects after this algorithm runs
ie. we dont need to use objects in this algorithm  but just match
student_nbr strings to other student_nbr strings

Example:   [student1: student2, student3, student4),
            student2: student1,student3,student4)]

If we do this we can get rid of 'assignment authors' dictionary
"""

######################  TESTING VARIABLES ########################

students = ["Charlie", "Jackie", "Fiona", "Sam",
            "Tom", "Patrick", "Marly"]
assignments = ["submission1", "submission2","submission3", "submission4",
               "submission5", "submission6", "submission7"]

nbr_reviews = 3 #nbr of reviews required per student, 

assignment_authors = {"Charlie": "submission1", "Jackie": "submission2",
                      "Fiona": "submission3", "Sam": "submission4",
            "Tom": "submission5", "Patrick": "submission6",
                      "Marly": "submission7"}

######################  END TESTING VARIABLES ########################


def swap_with_other_student(student, individual_allocations, random_assn,
                            alloc_mapping, assignment_authors, nbr_reviews):
    """Swaps unpermissable assignment with a student who already has been
    allocated their assignments, provided that other student is allowed to do
    assignment.

    Returns new permitted assignment allocate to student

    swap_with_other_student(str, list(str), str, dict(str:str), dict(str:str),
        int -> str
    """
    swap_range = len(alloc_mapping) - 1
    times_through_loop = 0
    while (times_through_loop <= swap_range):
        #select another student to swap with and access their allocations
        other_student = alloc_mapping.keys()[times_through_loop]
        allocated_list = alloc_mapping[other_student] 
        index = 0
        times_through_loop = times_through_loop + 1
        while (index < nbr_reviews):
            assn_to_test = allocated_list[index]
            #test_assignment must not be the same as random_assn
            if ((assn_to_test == random_assn) or
                #test_assignment must not be authored by student
            (assn_to_test == assignment_authors[student]== assn_to_test)
                #test_assignment must not already be allocated to student
            or (assn_to_test in individual_allocations) or
                #other_student must not have authored random_assn
            (assignment_authors[other_student] == random_assn)
                #other_student must not already have random_assn
            or (random_assn in allocated_list)):  
                index += 1  #move onto next one
            else:
                allocated_list[index] = random_assn
                return assn_to_test
       
    
    

def update_students_allocated(assignments, students_allocated,
                              random_assn,reviews_per_assn):
    """Updates the log of how many times each assignment has been allocated
    within the student pool, and removes the assignment when it has is receiving
    the total number of reviews that each assignment should get.
    
    update_students_allocated(list(str), dict(str: str), str, int -> None
    """
    students_allocated[random_assn] += 1
    if (students_allocated[random_assn] == reviews_per_assn):
        assignments.remove(random_assn)



def generate_individual_list(assignment_authors, individual_allocations,
                             assignments, students_allocated, reviews_per_assn,
                             nbr_reviews, alloc_mapping, j):
    """Generates an appropriate list of assignments for an individual student
    to review.

    Returns the list of individual assignments
    
    generate_individual_list(dict(str: str), list(str), list(str), 
        dict(str:int), int, int, dict(str:str), string -> list(str)
    """

    times_through_loop = 0
    while len(individual_allocations) < nbr_reviews:

        times_through_loop += 1
            
        if (len(assignments) == 0): break

        random_assn_nbr = random.randrange(len(assignments)) - 1
        random_assn = assignments[random_assn_nbr]
            
        #ensure student doesn't get their own or duplicate assignments
        if ((assignment_authors[j] != random_assn)
            and(random_assn not in individual_allocations)):
            individual_allocations.append(random_assn)
            update_students_allocated(assignments, students_allocated,
                                      random_assn, reviews_per_assn) 
            times_through_loop = 0
        elif ((times_through_loop > 10) and (len(assignments) < nbr_reviews)
              and (len(alloc_mapping) > 1)):
            #swap with another student who has already been allocated
            new = swap_with_other_student(j, individual_allocations, random_assn,
                alloc_mapping, assignment_authors, nbr_reviews)
            update_students_allocated(assignments, students_allocated,
                              random_assn, reviews_per_assn)
            #allocate swapped assignment to student
            individual_allocations.append(new) 
    return individual_allocations


def allocation(assignment_authors, students, assignments, nbr_reviews):
    """Allocates to students a list of assignnments to review, based on
    the number of reviews an instructor has specified for them to do

    Requires nbr_reviews < len(students) and len(assignments) >= len(students)

    Returns a mapping of students and assignments they are reviewing
    
    allocation(dict(str: str), list(str), list(str), int -> dict[str:str]
    """
     #find overall amount of marking to be done
    total_reviews = nbr_reviews* len(students)

    #find amount of reviews per assignment
    reviews_per_assn = total_reviews/len(assignments)

    #keep track of remainder if uneven
    remaining = total_reviews%len(assignments)

    #create dictionary to keep track of nbr_times_assigned
    #for each assignment
    students_allocated = {}
    for k in assignments:
        students_allocated[k] = 0        

    #create dictionary for allocations
    alloc_mapping = {}    
    for j in students:
        individual_allocations = []
            
        alloc_mapping[j] = generate_individual_list(assignment_authors, individual_allocations,
                             assignments, students_allocated, reviews_per_assn,
                             nbr_reviews, alloc_mapping, j)  

    return alloc_mapping