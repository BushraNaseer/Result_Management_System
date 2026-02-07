from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from .models import ClassRoom, Subject, Student, Result


# ---------------------------
# Register User
# ---------------------------
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("register")

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Account created successfully")
        return redirect("login")

    return render(request, "register.html")


# ---------------------------
# Login User
# ---------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password")
        return redirect("login")

    return render(request, "login.html")


# ---------------------------
# Dashboard
# ---------------------------
@login_required
def dashboard(request):
    # --------------------------
    # SAVE / UPDATE STUDENT & RESULTS
    # --------------------------
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        name = request.POST.get("name")
        roll_no = request.POST.get("roll_no")
        class_id = request.POST.get("class_name")
        
        try:
            classroom = ClassRoom.objects.get(id=class_id)
        except ClassRoom.DoesNotExist:
            messages.error(request, "Invalid class selection")
            return redirect("dashboard")

        # Create or update student
        if student_id:
            try:
                student = Student.objects.get(id=student_id)
                student.name = name
                student.roll_no = roll_no
                student.classroom = classroom
                student.save()
            except Student.DoesNotExist:
                messages.error(request, "Student not found")
                return redirect("dashboard")
        else:
            # Check if roll number already exists in the class
            if Student.objects.filter(roll_no=roll_no, classroom=classroom).exists():
                messages.error(request, "Roll number already exists in this class")
                return redirect("dashboard")
            
            student = Student.objects.create(name=name, roll_no=roll_no, classroom=classroom)

        # Save results
        results_saved = 0
        for sub in Subject.objects.all():
            marks_str = request.POST.get(f"subject_{sub.id}")
            if marks_str and marks_str.strip() != "":
                try:
                    marks = int(marks_str)
                    if marks < 0 or marks > 100:
                        messages.warning(request, f"Marks for {sub.name} should be between 0 and 100")
                        continue
                    
                    Result.objects.update_or_create(
                        student=student,
                        subject=sub,
                        defaults={"marks": marks}
                    )
                    results_saved += 1
                except ValueError:
                    messages.warning(request, f"Invalid marks entered for {sub.name}")

        messages.success(request, f"Student {'updated' if student_id else 'created'} successfully with {results_saved} subject(s)")
        return redirect("dashboard")

    # --------------------------
    # SHOW DASHBOARD
    # --------------------------
    classes = ClassRoom.objects.all()
    subjects = Subject.objects.all()

    # --------------------------
    # DYNAMIC SUMMARY
    # --------------------------
    total_students = Student.objects.count()
    
    # Count students who have at least one result - using Result model directly
    students_with_results_ids = Result.objects.values_list('student_id', flat=True).distinct()
    results_entered = len(students_with_results_ids)
    
    pass_students = 0
    fail_students = 0

    # Calculate pass/fail for students with results
    for student_id in students_with_results_ids:
        student_results = Result.objects.filter(student_id=student_id)
        entered_subjects = student_results.count()
        
        if entered_subjects > 0:
            # Pass if all subjects have marks >= 33
            if all(r.marks >= 33 for r in student_results):
                pass_students += 1
            else:
                fail_students += 1

    # --------------------------
    # RECENT RESULTS (Last 5 students with results)
    # --------------------------
    recent_results = []
    
    # Get last 5 students who have results
    recent_student_ids = Result.objects.values_list('student_id', flat=True).distinct().order_by('-student_id')[:5]
    recent_students = Student.objects.filter(id__in=recent_student_ids).order_by('-id')

    for student in recent_students:
        student_results = Result.objects.filter(student=student)
        total = sum(r.marks for r in student_results)
        entered_subjects = student_results.count()
        
        if entered_subjects > 0:
            percentage = (total / (entered_subjects * 100)) * 100
            status = "PASS" if all(r.marks >= 33 for r in student_results) else "FAIL"
            
            grade = "F"
            if status == "PASS":
                if percentage >= 80:
                    grade = 'A'
                elif percentage >= 60:
                    grade = 'B'
                elif percentage >= 40:
                    grade = 'C'
                else:
                    grade = 'D'
            
            # Add temporary attributes for template
            student.total_marks = total
            student.percentage = round(percentage, 2)
            student.status = status
            student.grade = grade
            student.subjects_count = entered_subjects
            
            recent_results.append(student)

    # --------------------------
    # EDIT STUDENT
    # --------------------------
    edit_student = None
    edit_results = {}
    edit_subject_status = {}

    edit_id = request.GET.get("edit")
    if edit_id:
        try:
            edit_student = Student.objects.get(id=edit_id)
            student_results = Result.objects.filter(student=edit_student)
            for r in student_results:
                edit_results[r.subject.id] = r.marks
                edit_subject_status[r.subject.id] = "PASS" if r.marks >= 33 else "FAIL"
        except Student.DoesNotExist:
            messages.warning(request, "Student not found")
            edit_student = None

    return render(request, "dashboard.html", {
        "classes": classes,
        "subjects": subjects,
        "total_students": total_students,
        "results_entered": results_entered,
        "pass_students": pass_students,
        "fail_students": fail_students,
        "recent_results": recent_results,
        "edit_student": edit_student,
        "edit_results": edit_results,
        "edit_subject_status": edit_subject_status,
    })


# ---------------------------
# Logout
# ---------------------------
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("login")














