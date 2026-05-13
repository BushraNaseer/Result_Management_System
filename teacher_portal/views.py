import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import ClassRoom, Subject, Student, Result


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("teacher_portal:register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("teacher_portal:register")

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Account created successfully")
        return redirect("teacher_portal:login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            return redirect("teacher_portal:dashboard")

        messages.error(request, "Invalid username or password")
        return redirect("teacher_portal:login")

    return render(request, "login.html")


@login_required
def dashboard(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        name = request.POST.get("name")
        roll_no = request.POST.get("roll_no")
        email = request.POST.get("email")
        class_id = request.POST.get("class_id") or request.GET.get("class_id")

        try:
            classroom = ClassRoom.objects.get(id=class_id)
        except ClassRoom.DoesNotExist:
            messages.error(request, "Invalid class selection")
            return redirect("teacher_portal:dashboard")

        if student_id:
            try:
                student = Student.objects.get(id=student_id)
                student.name = name
                student.roll_no = roll_no
                student.email = email
                student.classroom = classroom
                student.save()
            except Student.DoesNotExist:
                messages.error(request, "Student not found")
                return redirect("teacher_portal:dashboard")
        else:
            if Student.objects.filter(roll_no=roll_no, classroom=classroom).exclude(id=student_id).exists():
                messages.error(request, "Roll number already exists in this class")
                return redirect("teacher_portal:dashboard")

            student = Student.objects.create(name=name, roll_no=roll_no, email=email, classroom=classroom)

        results_saved = 0
        for sub in Subject.objects.filter(classes=classroom):
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
        return redirect("teacher_portal:dashboard")

    # --------------------------
    # Show Dashboard
    # --------------------------
    classes = ClassRoom.objects.all()
    class_id = request.GET.get("class_id")
    print("CLASS ID RECEIVED:", class_id)
    subjects = Subject.objects.none()
    if class_id:
        try:
            classroom = ClassRoom.objects.get(id=class_id)
            subjects = Subject.objects.filter(classes=classroom)
        except ClassRoom.DoesNotExist:
            subjects = Subject.objects.none()

    students = Student.objects.all()
    total_students = students.count()

    students_with_results = students.filter(results__isnull=False).distinct()
    results_entered = students_with_results.count()

    pass_students = 0
    fail_students = 0

    for student in students_with_results:
        student_results = Result.objects.filter(student=student)
        if student_results.exists():
            if all(r.marks >= 33 for r in student_results):
                pass_students += 1
            else:
                fail_students += 1

    # --------------------------
    # Recent Results (last 5 students)
    # --------------------------
    recent_results = []
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

            student.total_marks = total
            student.percentage = round(percentage, 2)
            student.status = status
            student.grade = grade
            student.subjects_count = entered_subjects

            recent_results.append(student)

    # --------------------------
    # Edit Student
    # --------------------------
    edit_student = None
    edit_results = {}
    edit_subject_status = {}
    edit_subjects = Subject.objects.none()

    edit_id = request.GET.get("edit")
    if edit_id:
        try:
            edit_student = Student.objects.get(id=edit_id)
            edit_subjects = Subject.objects.filter(classes=edit_student.classroom)
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
        "edit_subjects": edit_subjects,
        "edit_subject_status": edit_subject_status,
    })


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("teacher_portal:login")


@login_required
def export_class_results(request):
    class_id = request.GET.get('class_id')

    if not class_id:
        messages.error(request, "Please select a class to export.")
        return redirect("teacher_portal:dashboard")

    try:
        classroom = ClassRoom.objects.get(id=class_id)
    except ClassRoom.DoesNotExist:
        messages.error(request, "Class not found.")
        return redirect("teacher_portal:dashboard")

    students = Student.objects.filter(classroom=classroom).prefetch_related('results__subject').order_by('roll_no')
    subjects = Subject.objects.filter(classes=classroom).order_by('name')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Class {classroom.name}"

    header_font = Font(name='Arial', bold=True, color='FFFFFF', size=11)
    title_font  = Font(name='Arial', bold=True, size=14, color='1F3864')
    data_font   = Font(name='Arial', size=10)
    header_fill = PatternFill('solid', start_color='1F3864')
    alt_fill    = PatternFill('solid', start_color='DCE6F1')
    pass_fill   = PatternFill('solid', start_color='C6EFCE')
    fail_fill   = PatternFill('solid', start_color='FFC7CE')
    center      = Alignment(horizontal='center', vertical='center')
    thin        = Side(style='thin', color='AAAAAA')
    border      = Border(left=thin, right=thin, top=thin, bottom=thin)

    subject_count = subjects.count()
    total_cols    = 3 + subject_count + 4
    last_col      = get_column_letter(total_cols)

    ws.merge_cells(f'A1:{last_col}1')
    ws['A1'] = f"Result Sheet — Class {classroom.name}"
    ws['A1'].font      = title_font
    ws['A1'].alignment = center
    ws.row_dimensions[1].height = 32

    headers = ['Roll No', 'Student Name', 'Class'] + [sub.name for sub in subjects] + ['Total Marks', 'Percentage', 'Grade', 'Status']
    ws.append(headers)

    for col_num, header in enumerate(headers, start=1):
        cell           = ws.cell(row=2, column=col_num)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center
        cell.border    = border

    ws.row_dimensions[2].height = 20

    for idx, student in enumerate(students, start=1):
        results_map   = {r.subject.id: r.marks for r in student.results.all()}
        subject_marks = [results_map.get(sub.id, '-') for sub in subjects]

        numeric_marks = [m for m in subject_marks if isinstance(m, int)]
        total         = sum(numeric_marks)
        max_marks     = len(numeric_marks) * 100
        percentage    = round((total / max_marks) * 100, 2) if max_marks > 0 else 0
        status        = "PASS" if numeric_marks and all(m >= 33 for m in numeric_marks) else "FAIL"

        if status == "PASS":
            if percentage >= 80:   grade = 'A'
            elif percentage >= 60: grade = 'B'
            elif percentage >= 40: grade = 'C'
            else:                  grade = 'D'
        else:
            grade = 'F'

        row_data = [student.roll_no, student.name, classroom.name] + subject_marks + [total, f"{percentage}%", grade, status]
        ws.append(row_data)

        row_num  = idx + 2
        row_fill = alt_fill if idx % 2 == 0 else None

        for col_num in range(1, total_cols + 1):
            cell           = ws.cell(row=row_num, column=col_num)
            cell.font      = data_font
            cell.alignment = center
            cell.border    = border
            if row_fill:
                cell.fill  = row_fill

        status_cell      = ws.cell(row=row_num, column=total_cols)
        status_cell.fill = pass_fill if status == "PASS" else fail_fill
        status_cell.font = Font(name='Arial', bold=True, size=10)

    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 12
    for i in range(4, 4 + subject_count):
        ws.column_dimensions[get_column_letter(i)].width = 18
    ws.column_dimensions[get_column_letter(3 + subject_count + 1)].width = 14
    ws.column_dimensions[get_column_letter(3 + subject_count + 2)].width = 13
    ws.column_dimensions[get_column_letter(3 + subject_count + 3)].width = 10
    ws.column_dimensions[get_column_letter(3 + subject_count + 4)].width = 10

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Class_{classroom.name}_Results.xlsx"'
    wb.save(response)
    return response


# ✅ Notify Students by Email (Admin only)
@login_required
def notify_students(request):
    if not request.user.is_superuser:
        messages.error(request, "Only admin can send notifications.")
        return redirect("teacher_portal:dashboard")

    class_id = request.POST.get('class_id')

    if not class_id:
        messages.error(request, "Please select a class.")
        return redirect("teacher_portal:dashboard")

    try:
        classroom = ClassRoom.objects.get(id=class_id)
    except ClassRoom.DoesNotExist:
        messages.error(request, "Class not found.")
        return redirect("teacher_portal:dashboard")

    students = Student.objects.filter(classroom=classroom).prefetch_related('results__subject')
    sent = 0
    skipped = 0

    for student in students:
        print(f"Student: {student.name}, Email: {student.email}, Has results: {student.results.exists()}")
        if not student.email:
            skipped += 1
            continue

        student_results = student.results.all()
        if not student_results.exists():
            skipped += 1
            continue

        total = sum(r.marks for r in student_results)
        max_marks = student_results.count() * 100
        percentage = round((total / max_marks) * 100, 2) if max_marks > 0 else 0
        status = "PASS" if all(r.marks >= 33 for r in student_results) else "FAIL"

        if status == "PASS":
            if percentage >= 80:   grade = 'A'
            elif percentage >= 60: grade = 'B'
            elif percentage >= 40: grade = 'C'
            else:                  grade = 'D'
        else:
            grade = 'F'

        subject_lines = "\n".join(
            f"  {r.subject.name}: {r.marks}/100 ({'PASS' if r.marks >= 33 else 'FAIL'})"
            for r in student_results
        )

        message = f"""Dear {student.name},

Your result for Class {classroom.name} has been uploaded.

Result Summary:
{subject_lines}

Total Marks : {total} / {max_marks}
Percentage  : {percentage}%
Grade       : {grade}
Status      : {status}

Please contact your teacher if you have any questions.

Regards,
School Administration"""

        try:
            send_mail(
                subject=f"Your Result Has Been Uploaded — Class {classroom.name}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=False,
            )
            sent += 1
        except Exception as e:
            print(f"EMAIL ERROR for {student.name}: {e}")
            skipped += 1

    messages.success(request, f"Emails sent to {sent} student(s). {skipped} skipped (no email or no results).")
    return redirect("teacher_portal:dashboard")