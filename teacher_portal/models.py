from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class ClassRoom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Class Room'
        verbose_name_plural = 'Class Rooms'

    def __str__(self):
        return self.name

    def get_total_students(self):
        return self.student_set.count()


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    classes = models.ManyToManyField(ClassRoom, related_name='subjects', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_no = models.IntegerField(validators=[MinValueValidator(1)])
    email = models.EmailField(blank=True, null=True)  # ✅ NEW
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='students')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['classroom', 'roll_no']
        unique_together = ['roll_no', 'classroom']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.name} ({self.roll_no}) - {self.classroom.name}"

    def get_total_marks(self):
        return sum(result.marks for result in self.result_set.all())

    def get_percentage(self):
        results = self.result_set.all()
        if not results:
            return 0
        total = sum(r.marks for r in results)
        max_marks = results.count() * 100
        return round((total / max_marks) * 100, 2) if max_marks > 0 else 0

    def get_status(self):
        results = self.result_set.all()
        if not results:
            return "NO RESULTS"
        return "PASS" if all(r.marks >= 33 for r in results) else "FAIL"

    def get_grade(self):
        percentage = self.get_percentage()
        status = self.get_status()

        if status != "PASS":
            return "F"

        if percentage >= 80:
            return 'A'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 40:
            return 'C'
        elif percentage >= 33:
            return 'D'
        else:
            return 'F'

    def get_position_in_class(self):
        students = Student.objects.filter(classroom=self.classroom)
        student_data = []

        for student in students:
            results = student.result_set.all()
            if results.exists():
                total = sum(r.marks for r in results)
                percentage = student.get_percentage()
                status = student.get_status()

                if status == "PASS":
                    student_data.append({
                        'id': student.id,
                        'total': total,
                        'percentage': percentage
                    })

        student_data.sort(key=lambda x: x['percentage'], reverse=True)

        for index, data in enumerate(student_data, start=1):
            if data['id'] == self.id:
                return index

        return "-"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='results')
    marks = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Marks should be between 0 and 100"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student', 'subject']
        unique_together = ['student', 'subject']
        verbose_name = 'Result'
        verbose_name_plural = 'Results'

    def __str__(self):
        return f"{self.student.name} - {self.subject.name}: {self.marks}"

    def get_status(self):
        return "PASS" if self.marks >= 33 else "FAIL"

    def get_grade(self):
        if self.marks >= 80:
            return 'A'
        elif self.marks >= 60:
            return 'B'
        elif self.marks >= 40:
            return 'C'
        elif self.marks >= 33:
            return 'D'
        else:
            return 'F'
