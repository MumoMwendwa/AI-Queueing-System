from django.contrib import admin
from .models import Doctor, Patient, QueueTicket, Notification, Department, VirtualCard, MedicalRecord


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'room_number', 'is_available')
    list_filter = ('specialization', 'is_available')
    search_fields = ('user__username', 'specialization')


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'contact_number', 'registered_at')
    search_fields = ('user__username', 'contact_number')
    readonly_fields = ('registered_at',)  # removed virtual_card_id


@admin.register(QueueTicket)
class QueueAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'patient', 'doctor', 'check_in_time', 'status')
    list_filter = ('status', 'doctor')
    search_fields = ('ticket_number', 'patient__user__username', 'doctor__user__username')
    readonly_fields = ('ticket_number', 'check_in_time')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'message')
    readonly_fields = ('created_at',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'current_queue_number')
    search_fields = ('name',)


@admin.register(VirtualCard)
class VirtualCardAdmin(admin.ModelAdmin):
    list_display = ('patient', 'virtual_card_id', 'has_physical_card', 'registration_date')
    readonly_fields = ('virtual_card_id', 'registration_date')
    search_fields = ('patient__user__username', 'virtual_card_id')


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'visit_date', 'diagnosis', 'follow_up_required')
    list_filter = ('follow_up_required', 'visit_date')
    search_fields = ('patient__user__username', 'doctor__user__username')
    readonly_fields = ('visit_date',)


# Customize admin site titles
admin.site.site_header = "AI Queueing System Admin"
admin.site.site_title = "AI Queueing System Admin Portal"
admin.site.index_title = "Welcome to the AI Queueing System Administration"
