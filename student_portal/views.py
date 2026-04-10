from django.shortcuts import render
from teacher_portal.models import Student, Result
from django.utils.timezone import now

def roll_search(request):
    print("VIEW HIT")

    if request.method == "POST":
        rollno = request.POST.get("rollno", "").strip()
        print("ROLL FROM FORM =", rollno)

        if not rollno:
            return render(request, "student_portal/display_page.html",
                          {"error": "Please enter a roll number"})

        try:
            rollno = int(rollno)
        except ValueError:
            return render(request, "student_portal/display_page.html",
                          {"error": "Roll number must be numeric"})

        try:
            student = Student.objects.get(roll_no=rollno)
            results = Result.objects.filter(student=student)

            if not results.exists():
                return render(request, "student_portal/display_page.html",
                              {"error": "No results found for this student"})

            # ✅ TOTAL CALCULATION
            total_marks = sum(r.marks for r in results)
            max_marks = results.count() * 100
            percentage = round((total_marks / max_marks) * 100, 2)

            # ✅ FIX FOR CHART (IMPORTANT)
            subjects = list(results.values_list('subject__name', flat=True))
            marks = list(results.values_list('marks', flat=True))

            context = {
                "student": student,
                "results": results,

                # ✅ CHART DATA (FIXED)
                "subjects": subjects,
                "marks": marks,

                "total_marks": total_marks,
                "max_marks": max_marks,
                "percentage": percentage,
                "today": now(),
                "show_result": True,
            }

            return render(request, "student_portal/display_result.html", context)

        except Student.DoesNotExist:
            return render(request, "student_portal/display_page.html",
                          {"error": "No student found with this roll number"})

    return render(request, "student_portal/display_page.html")











