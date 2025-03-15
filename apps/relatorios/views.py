import io
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from apps.alunos.models import Aluno, TurnoChoices
from django.http import FileResponse
from django.db.models import Avg, Count
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from apps.alunos.models import Aluno, Nota

def is_teacher_or_admin(user):
    return user.groups.filter(name__in=['Professores', 'Administradores']).exists()

def gerar_pdf(data, titulo, colunas):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(titulo, styles['Title']))
    tabela_data = [colunas] + data
    tabela = Table(tabela_data)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(tabela)
    doc.build(elements)
    buffer.seek(0)
    return buffer

@login_required
@user_passes_test(is_teacher_or_admin)
def relatorios(request):
    # Get total students
    total_alunos = Aluno.objects.filter(ativo=True).count()
    
    # Get total unique classes
    total_turmas = Aluno.objects.filter(ativo=True).values('turma').distinct().count()
    
    # Get students by shift
    alunos_manha = Aluno.objects.filter(ativo=True, turno='M').count()
    alunos_tarde = Aluno.objects.filter(ativo=True, turno='T').count()
    
    # Get students by education level (EFI - Anos Iniciais, EFF - Anos Finais)
    alunos_efi = Aluno.objects.filter(
        ativo=True,
        ano__in=['3', '4', '5']  # Changed from serie to ano
    ).count()
    
    alunos_eff = Aluno.objects.filter(
        ativo=True,
        ano__in=['6', '7', '8', '9']  # Changed from serie to ano
    ).count()
    
    # Get students by grade
    alunos_3ano = Aluno.objects.filter(ativo=True, ano='3').count()
    alunos_4ano = Aluno.objects.filter(ativo=True, ano='4').count()
    alunos_5ano = Aluno.objects.filter(ativo=True, ano='5').count()
    alunos_6ano = Aluno.objects.filter(ativo=True, ano='6').count()
    alunos_7ano = Aluno.objects.filter(ativo=True, ano='7').count()
    alunos_8ano = Aluno.objects.filter(ativo=True, ano='8').count()
    alunos_9ano = Aluno.objects.filter(ativo=True, ano='9').count()

    context = {
        'total_alunos': total_alunos,
        'total_turmas': total_turmas,
        'alunos_manha': alunos_manha,
        'alunos_tarde': alunos_tarde,
        'alunos_efi': alunos_efi,
        'alunos_eff': alunos_eff,
        'alunos_3ano': alunos_3ano,
        'alunos_4ano': alunos_4ano,
        'alunos_5ano': alunos_5ano,
        'alunos_6ano': alunos_6ano,
        'alunos_7ano': alunos_7ano,
        'alunos_8ano': alunos_8ano,
        'alunos_9ano': alunos_9ano,
    }
    
    return render(request, 'relatorios/relatorios.html', context)

@login_required
@user_passes_test(is_teacher_or_admin)
def relatorio_media_por_serie(request):
    media_por_serie = Nota.objects.values('aluno__serie').annotate(media=Avg('valor'))
    return render(request, 'relatorios/media_por_serie.html', {'media_por_serie': media_por_serie})

@login_required
@user_passes_test(is_teacher_or_admin)
def exportar_media_por_serie_pdf(request):
    media_por_serie = Nota.objects.values('aluno__serie').annotate(media=Avg('valor'))
    data = [[item['aluno__serie'], f"{item['media']:.2f}"] for item in media_por_serie]
    colunas = ['Série', 'Média']
    pdf_buffer = gerar_pdf(data, 'Relatório de Média por Série', colunas)
    return FileResponse(pdf_buffer, as_attachment=True, filename='media_por_serie.pdf')

@login_required
@user_passes_test(is_teacher_or_admin)
def relatorio_alunos_por_serie(request):
    alunos_por_serie = Aluno.objects.values('serie').annotate(total=Count('id'))
    return render(request, 'relatorios/alunos_por_serie.html', {'alunos_por_serie': alunos_por_serie})

@login_required
@user_passes_test(is_teacher_or_admin)
def exportar_alunos_por_serie_pdf(request):
    alunos_por_serie = Aluno.objects.values('serie').annotate(total=Count('id'))
    data = [[item['serie'], str(item['total'])] for item in alunos_por_serie]
    colunas = ['Série', 'Total de Alunos']
    pdf_buffer = gerar_pdf(data, 'Relatório de Alunos por Série', colunas)
    return FileResponse(pdf_buffer, as_attachment=True, filename='alunos_por_serie.pdf')

@login_required
@user_passes_test(is_teacher_or_admin)
def relatorio_notas_baixas(request):
    notas_baixas = Nota.objects.filter(valor__lt=6).select_related('aluno')
    return render(request, 'relatorios/notas_baixas.html', {'notas_baixas': notas_baixas})

@login_required
@user_passes_test(is_teacher_or_admin)
def exportar_notas_baixas_pdf(request):
    notas_baixas = Nota.objects.filter(valor__lt=6).select_related('aluno')
    data = [[nota.aluno.nome, nota.aluno.serie, nota.disciplina, f"{nota.valor:.2f}", nota.data.strftime('%d/%m/%Y')] for nota in notas_baixas]
    colunas = ['Aluno', 'Série', 'Disciplina', 'Nota', 'Data']
    pdf_buffer = gerar_pdf(data, 'Relatório de Notas Baixas', colunas)
    return FileResponse(pdf_buffer, as_attachment=True, filename='notas_baixas.pdf')