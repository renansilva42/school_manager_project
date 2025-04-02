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
    
    # Dentro do método get_student_info, atualize a busca por nome para ser mais flexível

    def get_student_info(self, student_id=None, name=None, matricula=None):
        """
        Busca informações completas de um aluno pelo ID, nome ou matrícula
        Retorna todos os dados disponíveis no modelo Aluno para que o chatbot
        possa responder perguntas específicas sobre qualquer informação do aluno.
        """
        try:
            # Identificar o aluno
            aluno = None
            
            # Se a matrícula for informada, buscar diretamente por ela
            if matricula:
                try:
                    # Garantir que a matrícula seja tratada corretamente
                    aluno = Aluno.objects.filter(matricula=str(matricula)).first()
                except Exception as e:
                    logger.error(f"Erro ao buscar por matrícula {matricula}: {str(e)}")
                    return {"error": f"Erro ao buscar por matrícula: {str(e)}"}
                    
                if not aluno:
                    logger.warning(f"Aluno não encontrado com matrícula: {matricula}")
                    return {"error": "Aluno não encontrado com a matrícula informada"}
            
            # Caso seja informado um student_id, fazer busca por ID
            elif student_id:
                try:
                    aluno = Aluno.objects.filter(id=student_id).first()
                except Exception as e:
                    logger.error(f"Erro ao buscar por ID {student_id}: {str(e)}")
                    return {"error": f"Erro ao buscar por ID: {str(e)}"}
                    
                if not aluno:
                    logger.warning(f"Aluno não encontrado com ID: {student_id}")
                    return {"error": "Aluno não encontrado pelo ID"}
            
            # Se for informado o nome, realizar busca aproximada
            elif name:
                # Prepara o nome para busca - remove caracteres especiais e normaliza
                try:
                    import unicodedata
                    from django.db.models import Q
                    
                    # Normaliza o nome removendo acentos 
                    def normalizar_nome(nome):
                        nome = unicodedata.normalize('NFKD', nome)
                        nome = ''.join([c for c in nome if not unicodedata.combining(c)])
                        return nome.upper()
                    
                    nome_normalizado = normalizar_nome(name)
                    logger.info(f"Buscando aluno com nome normalizado: {nome_normalizado}")
                    
                    # Verificar se o nome é válido
                    if not name or not isinstance(name, str):
                        logger.error(f"Nome inválido fornecido para busca: {name}")
                        return {"error": "Nome inválido fornecido para busca"}
                    
                    # Busca direta pelo nome
                    alunos = Aluno.objects.filter(nome__icontains=name)
                    
                    # Se não encontrou, tenta busca com nome normalizado
                    if alunos.count() == 0:
                        # Busca por palavras individuais do nome
                        termos = nome_normalizado.split()
                        query = Q()
                        for termo in termos:
                            if len(termo) > 2:  # Ignorar termos muito curtos
                                query |= Q(nome__icontains=termo)
                        
                        alunos = Aluno.objects.filter(query)
                    
                    if alunos.count() == 0:
                        return {"error": "Aluno não encontrado com o nome informado"}
                    elif alunos.count() > 1:
                        try:
                            alunos_list = []
                            for a in alunos:
                                if isinstance(a, Aluno):
                                    alunos_list.append({"id": a.id, "nome": a.nome, "matricula": a.matricula})
                                else:
                                    logger.warning(f"Objeto não é um Aluno: {type(a)}")
                            
                            return {
                                "message": f"Encontrados {len(alunos_list)} alunos com esse nome",
                                "alunos": alunos_list
                            }
                        except Exception as e:
                            logger.error(f"Erro ao processar lista de alunos: {str(e)}")
                            return {"error": f"Erro ao processar lista de alunos: {str(e)}"}
                    # Verificar se encontrou algum aluno
                    if alunos.count() > 0:
                        aluno = alunos.first()
                        # Verificar se o objeto aluno é válido
                        if not isinstance(aluno, Aluno):
                            logger.error(f"Objeto retornado não é um Aluno: {type(aluno)}")
                            return {"error": f"Erro interno: objeto retornado não é um Aluno"}
                    else:
                        logger.warning(f"Nenhum aluno encontrado com o nome: {name}")
                        return {"error": f"Nenhum aluno encontrado com o nome: {name}"}
                except Exception as e:
                    logger.error(f"Erro ao buscar por nome {name}: {str(e)}")
                    return {"error": f"Erro ao buscar por nome: {str(e)}"}
            
            else:
                return {"error": "É necessário fornecer matrícula, ID ou nome do aluno"}
            
            # Verificação adicional para garantir que aluno não seja None ou um tipo não esperado
            if not aluno:
                logger.error("Aluno não foi identificado corretamente após as buscas")
                return {"error": "Aluno não encontrado após buscas"}
                
            if isinstance(aluno, str):
                logger.error(f"Objeto aluno é uma string: {aluno}")
                return {"error": f"Erro interno: o objeto aluno é uma string, não um objeto Aluno"}
            elif not isinstance(aluno, Aluno):
                logger.error(f"Objeto aluno é do tipo inesperado: {type(aluno)}")
                return {"error": f"Erro interno: o objeto aluno é do tipo {type(aluno)}, não do tipo Aluno"}
            
            # Construir resposta completa com todos os dados disponíveis do aluno
            idade = aluno.get_idade() if hasattr(aluno, 'get_idade') else None
            foto_url = aluno.get_foto_url() if hasattr(aluno, 'get_foto_url') else None
            
            # Obter o display de campos com choices
            try:
                nivel_display = aluno.get_nivel_display()
            except Exception as e:
                logger.debug(f"Erro ao obter nivel_display: {str(e)}")
                nivel_display = aluno.nivel
                
            try:
                turno_display = aluno.get_turno_display()
            except Exception as e:
                logger.debug(f"Erro ao obter turno_display: {str(e)}")
                turno_display = aluno.turno
                
            try:
                ano_display = aluno.get_ano_display()
            except Exception as e:
                logger.debug(f"Erro ao obter ano_display: {str(e)}")
                ano_display = aluno.ano
            
            # Estruturar resposta em categorias para facilitar a interpretação
            resposta = {
                "id": aluno.id,
                "status": "Ativo" if aluno.ativo else "Inativo",
                
                "dados_pessoais": {
                    "nome": aluno.nome,
                    "matricula": aluno.matricula,
                    "cpf": aluno.cpf,
                    "rg": aluno.rg,
                    "data_nascimento": aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else None,
                    "idade": idade,
                    "foto_url": foto_url
                },
                
                "contato": {
                    "email": aluno.email,
                    "telefone": aluno.telefone
                },
                
                "endereco": {
                    "logradouro": aluno.endereco,
                    "cidade": aluno.cidade,
                    "uf": aluno.uf
                },
                
                "dados_academicos": {
                    "nivel": nivel_display,
                    "turno": turno_display,
                    "ano": ano_display,
                    "turma": aluno.turma.nome if hasattr(aluno, 'turma') and aluno.turma else None,
                    "data_matricula": aluno.data_matricula.strftime('%d/%m/%Y') if hasattr(aluno, 'data_matricula') and aluno.data_matricula else None
                },
                
                "responsaveis": [
                    {
                        "nome": aluno.nome_responsavel1,
                        "telefone": aluno.telefone_responsavel1
                    }
                ],
                
                "informacoes_adicionais": {
                    "observacoes": aluno.observacoes,
                    "dados_json": aluno.dados_adicionais,
                    "versao_cadastro": aluno.version,
                    "data_criacao": aluno.created_at.strftime('%d/%m/%Y %H:%M:%S') if hasattr(aluno, 'created_at') and aluno.created_at else None
                }
            }
            
            # Adicionar segundo responsável se existir
            if hasattr(aluno, 'nome_responsavel2') and aluno.nome_responsavel2:
                resposta["responsaveis"].append({
                    "nome": aluno.nome_responsavel2,
                    "telefone": aluno.telefone_responsavel2
                })
            
            return resposta
        except Exception as e:
            logger.error(f"Erro ao buscar informações do aluno: {str(e)}")
            return {"error": f"Erro ao buscar informações: {str(e)}"}
    
    def get_student_grades(self, student_id=None, name=None, matricula=None):
        """
        Busca as notas de um aluno
        """
        try:
            # Primeiro, identificar o aluno
            aluno = None
            if matricula:
                aluno = Aluno.objects.filter(matricula=matricula).first()
            elif student_id:
                aluno = Aluno.objects.filter(id=student_id).first()
            elif name:
                # Verificar se o nome é válido
                if not name or not isinstance(name, str):
                    logger.error(f"Nome inválido fornecido para busca: {name}")
                    return {"error": "Nome inválido fornecido para busca"}
                
                alunos = Aluno.objects.filter(nome__icontains=name)
                if alunos.count() == 1:
                    aluno = alunos.first()
                    # Verificar se o objeto aluno é válido
                    if not isinstance(aluno, Aluno):
                        logger.error(f"Objeto retornado não é um Aluno: {type(aluno)}")
                        return {"error": f"Erro interno: objeto retornado não é um Aluno"}
                elif alunos.count() > 1:
                    try:
                        alunos_list = []
                        for a in alunos:
                            if isinstance(a, Aluno):
                                alunos_list.append({"id": a.id, "nome": a.nome})
                            else:
                                logger.warning(f"Objeto não é um Aluno: {type(a)}")
                        
                        return {
                            "message": f"Encontrados {len(alunos_list)} alunos com esse nome",
                            "alunos": alunos_list
                        }
                    except Exception as e:
                        logger.error(f"Erro ao processar lista de alunos: {str(e)}")
                        return {"error": f"Erro ao processar lista de alunos: {str(e)}"}
            
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
    
    def analyze_student_performance(self, student_id=None, name=None, matricula=None):
        """
        Analisa o desempenho acadêmico de um aluno
        """
        try:
            # Primeiro, identificar o aluno
            aluno = None
            if matricula:
                aluno = Aluno.objects.filter(matricula=matricula).first()
            elif student_id:
                aluno = Aluno.objects.filter(id=student_id).first()
            elif name:
                # Verificar se o nome é válido
                if not name or not isinstance(name, str):
                    logger.error(f"Nome inválido fornecido para busca: {name}")
                    return {"error": "Nome inválido fornecido para busca"}
                
                alunos = Aluno.objects.filter(nome__icontains=name)
                if alunos.count() == 1:
                    aluno = alunos.first()
                    # Verificar se o objeto aluno é válido
                    if not isinstance(aluno, Aluno):
                        logger.error(f"Objeto retornado não é um Aluno: {type(aluno)}")
                        return {"error": f"Erro interno: objeto retornado não é um Aluno"}
                elif alunos.count() > 1:
                    try:
                        alunos_list = []
                        for a in alunos:
                            if isinstance(a, Aluno):
                                alunos_list.append({"id": a.id, "nome": a.nome})
                            else:
                                logger.warning(f"Objeto não é um Aluno: {type(a)}")
                        
                        return {
                            "message": f"Encontrados {len(alunos_list)} alunos com esse nome",
                            "alunos": alunos_list
                        }
                    except Exception as e:
                        logger.error(f"Erro ao processar lista de alunos: {str(e)}")
                        return {"error": f"Erro ao processar lista de alunos: {str(e)}"}
            
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
