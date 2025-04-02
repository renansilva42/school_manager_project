from django.db.models import Q, Avg
from apps.alunos.models import Aluno, Nota
import logging

# Configurar o logger
logger = logging.getLogger(__name__)

class ChatbotDatabaseConnector:
    """
    Classe para gerenciar a conexão do chatbot com o banco de dados
    utilizando os modelos Django existentes.
    """
    
    def __init__(self):
        logger.info("Inicializando conector de banco de dados do chatbot")
    
    def get_student_info(self, student_id=None, name=None):
        """
        Busca informações de um aluno pelo ID ou nome
        """
        try:
            if student_id:
                aluno = Aluno.objects.filter(id=student_id).first()
                if aluno:
                    return {
                        "id": aluno.id,
                        "nome": aluno.nome,
                        "matricula": aluno.matricula,
                        "data_nascimento": aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else None,
                        "turma": aluno.turma.nome if aluno.turma else None
                    }
                return {"error": "Aluno não encontrado"}
            
            elif name:
                # Busca aproximada por nome
                alunos = Aluno.objects.filter(nome__icontains=name)
                if alunos.count() == 1:
                    aluno = alunos.first()
                    return {
                        "id": aluno.id,
                        "nome": aluno.nome,
                        "matricula": aluno.matricula,
                        "data_nascimento": aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else None,
                        "turma": aluno.turma.nome if aluno.turma else None
                    }
                elif alunos.count() > 1:
                    return {
                        "message": f"Encontrados {alunos.count()} alunos com esse nome",
                        "alunos": [{"id": a.id, "nome": a.nome} for a in alunos]
                    }
                return {"error": "Aluno não encontrado"}
            
            return {"error": "É necessário fornecer ID ou nome do aluno"}
        except Exception as e:
            logger.error(f"Erro ao buscar informações do aluno: {str(e)}")
            return {"error": f"Erro ao buscar informações: {str(e)}"}
    
    def get_student_grades(self, student_id=None, name=None):
        """
        Busca as notas de um aluno
        """
        try:
            # Primeiro, identificar o aluno
            aluno = None
            if student_id:
                aluno = Aluno.objects.filter(id=student_id).first()
            elif name:
                alunos = Aluno.objects.filter(nome__icontains=name)
                if alunos.count() == 1:
                    aluno = alunos.first()
                elif alunos.count() > 1:
                    return {
                        "message": f"Encontrados {alunos.count()} alunos com esse nome",
                        "alunos": [{"id": a.id, "nome": a.nome} for a in alunos]
                    }
            
            if not aluno:
                return {"error": "Aluno não encontrado"}
            
            # Buscar as notas
            notas = Nota.objects.filter(aluno=aluno)
            if not notas.exists():
                return {
                    "aluno": {"id": aluno.id, "nome": aluno.nome},
                    "message": "Não há notas registradas para este aluno"
                }
            
            # Formatar as notas por disciplina
            notas_por_disciplina = {}
            for nota in notas:
                disciplina = nota.disciplina.nome if nota.disciplina else "Sem disciplina"
                if disciplina not in notas_por_disciplina:
                    notas_por_disciplina[disciplina] = []
                
                notas_por_disciplina[disciplina].append({
                    "valor": nota.valor,
                    "data": nota.data.strftime('%d/%m/%Y') if nota.data else None,
                    "descricao": nota.descricao
                })
            
            return {
                "aluno": {"id": aluno.id, "nome": aluno.nome},
                "notas": notas_por_disciplina
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar notas do aluno: {str(e)}")
            return {"error": f"Erro ao buscar notas: {str(e)}"}
    
    def analyze_student_performance(self, student_id=None, name=None):
        """
        Analisa o desempenho acadêmico de um aluno
        """
        try:
            # Primeiro, identificar o aluno
            aluno = None
            if student_id:
                aluno = Aluno.objects.filter(id=student_id).first()
            elif name:
                alunos = Aluno.objects.filter(nome__icontains=name)
                if alunos.count() == 1:
                    aluno = alunos.first()
                elif alunos.count() > 1:
                    return {
                        "message": f"Encontrados {alunos.count()} alunos com esse nome",
                        "alunos": [{"id": a.id, "nome": a.nome} for a in alunos]
                    }
            
            if not aluno:
                return {"error": "Aluno não encontrado"}
            
            # Buscar as notas
            notas = Nota.objects.filter(aluno=aluno)
            if not notas.exists():
                return {
                    "aluno": {"id": aluno.id, "nome": aluno.nome},
                    "message": "Não há notas registradas para análise de desempenho"
                }
            
            # Calcular médias por disciplina
            medias_por_disciplina = {}
            for nota in notas:
                disciplina = nota.disciplina.nome if nota.disciplina else "Sem disciplina"
                if disciplina not in medias_por_disciplina:
                    medias_por_disciplina[disciplina] = {"soma": 0, "count": 0}
                
                medias_por_disciplina[disciplina]["soma"] += nota.valor
                medias_por_disciplina[disciplina]["count"] += 1
            
            # Calcular média geral e formatar resultados
            media_geral = 0
            total_notas = 0
            analise = {}
            
            for disciplina, dados in medias_por_disciplina.items():
                media = dados["soma"] / dados["count"]
                analise[disciplina] = {
                    "media": round(media, 2),
                    "status": "Aprovado" if media >= 7 else "Em recuperação" if media >= 5 else "Reprovado"
                }
                media_geral += media
                total_notas += 1
            
            if total_notas > 0:
                media_geral = round(media_geral / total_notas, 2)
            
            # Buscar média da turma para comparação
            media_turma = 0
            if aluno.turma:
                media_turma_query = Nota.objects.filter(
                    aluno__turma=aluno.turma
                ).aggregate(media=Avg('valor'))
                
                if media_turma_query['media']:
                    media_turma = round(media_turma_query['media'], 2)
            
            return {
                "aluno": {"id": aluno.id, "nome": aluno.nome},
                "media_geral": media_geral,
                "media_turma": media_turma,
                "status_geral": "Aprovado" if media_geral >= 7 else "Em recuperação" if media_geral >= 5 else "Reprovado",
                "comparacao_turma": "Acima da média" if media_geral > media_turma else 
                                   "Na média" if media_geral == media_turma else "Abaixo da média",
                "analise_por_disciplina": analise
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar desempenho do aluno: {str(e)}")
            return {"error": f"Erro ao analisar desempenho: {str(e)}"}
