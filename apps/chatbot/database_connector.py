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

    def get_student_info(self, student_id=None, name=None, matricula=None, fields=None):
        """
        Busca informações de um aluno pelo ID, nome ou matrícula
        Retorna todos os dados disponíveis no modelo Aluno ou apenas os campos especificados
        para que o chatbot possa responder perguntas específicas sobre o aluno.
        
        Args:
            student_id: ID do aluno
            name: Nome do aluno
            matricula: Matrícula do aluno
            fields: Lista de campos a serem retornados. Se None, retorna todos os campos.
                   Pode conter categorias como 'dados_pessoais', 'contato', 'endereco',
                   'dados_academicos', 'responsaveis', 'informacoes_adicionais',
                   ou campos específicos como 'nome', 'email', etc.
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
                    
                    # Verificar se o modelo Aluno está sendo importado corretamente
                    logger.info(f"Verificando modelo Aluno: {Aluno.__module__}.{Aluno.__name__}")
                    
                    # Busca direta pelo nome com debug
                    logger.info(f"Iniciando busca por nome: '{name}'")
                    try:
                        alunos = list(Aluno.objects.filter(nome__icontains=name))
                        logger.info(f"Busca direta encontrou {len(alunos)} alunos")
                        
                        # Verificar o tipo de cada objeto retornado
                        for i, a in enumerate(alunos):
                            logger.info(f"Aluno {i+1}: tipo={type(a)}, repr={repr(a)}")
                            
                        # Se não encontrou, tenta busca com nome normalizado
                        if len(alunos) == 0:
                            # Busca por palavras individuais do nome
                            termos = nome_normalizado.split()
                            query = Q()
                            for termo in termos:
                                if len(termo) > 2:  # Ignorar termos muito curtos
                                    query |= Q(nome__icontains=termo)
                            
                            logger.info(f"Tentando busca alternativa com termos: {termos}")
                            alunos_query = Aluno.objects.filter(query)
                            alunos = list(alunos_query)
                            logger.info(f"Busca alternativa encontrou {len(alunos)} alunos")
                            
                            # Verificar o tipo de cada objeto retornado
                            for i, a in enumerate(alunos):
                                logger.info(f"Aluno alternativo {i+1}: tipo={type(a)}, repr={repr(a)}")
                    except Exception as e:
                        logger.error(f"Erro durante a busca de alunos: {str(e)}")
                        return {"error": f"Erro durante a busca de alunos: {str(e)}"}
                    
                    if len(alunos) == 0:
                        return {"error": "Aluno não encontrado com o nome informado"}
                    elif len(alunos) > 1:
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
                    if len(alunos) > 0:
                        # Como agora alunos é uma lista, usamos indexação em vez de first()
                        aluno = alunos[0]
                        logger.info(f"Selecionando primeiro aluno: tipo={type(aluno)}, repr={repr(aluno)}")
                        
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
            resposta_completa = {
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
                    "turma": aluno.turma if hasattr(aluno, 'turma') and aluno.turma else None,
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
                resposta_completa["responsaveis"].append({
                    "nome": aluno.nome_responsavel2,
                    "telefone": aluno.telefone_responsavel2
                })
            
            # Se não foram especificados campos, retornar todos os dados
            if not fields:
                return resposta_completa
            
            # Caso contrário, filtrar os campos solicitados
            resposta_filtrada = {"id": aluno.id}
            
            # Mapeamento de campos específicos para suas categorias
            campo_para_categoria = {
                "nome": "dados_pessoais",
                "matricula": "dados_pessoais",
                "cpf": "dados_pessoais",
                "rg": "dados_pessoais",
                "data_nascimento": "dados_pessoais",
                "idade": "dados_pessoais",
                "foto_url": "dados_pessoais",
                "email": "contato",
                "telefone": "contato",
                "logradouro": "endereco",
                "cidade": "endereco",
                "uf": "endereco",
                "nivel": "dados_academicos",
                "turno": "dados_academicos",
                "ano": "dados_academicos",
                "turma": "dados_academicos",
                "data_matricula": "dados_academicos",
                "observacoes": "informacoes_adicionais",
                "dados_json": "informacoes_adicionais",
                "versao_cadastro": "informacoes_adicionais",
                "data_criacao": "informacoes_adicionais"
            }
            
            # Processar cada campo solicitado
            for field in fields:
                # Se o campo é uma categoria principal, incluir toda a categoria
                if field in resposta_completa:
                    resposta_filtrada[field] = resposta_completa[field]
                # Se o campo é um campo específico, incluir apenas esse campo
                elif field in campo_para_categoria:
                    categoria = campo_para_categoria[field]
                    if categoria not in resposta_filtrada:
                        resposta_filtrada[categoria] = {}
                    resposta_filtrada[categoria][field] = resposta_completa[categoria][field]
                # Caso especial para responsáveis
                elif field == "responsavel" or field == "responsaveis":
                    resposta_filtrada["responsaveis"] = resposta_completa["responsaveis"]
            
            # Garantir que pelo menos o nome do aluno esteja sempre incluído
            if "dados_pessoais" not in resposta_filtrada:
                resposta_filtrada["dados_pessoais"] = {"nome": aluno.nome}
            elif "nome" not in resposta_filtrada["dados_pessoais"]:
                resposta_filtrada["dados_pessoais"]["nome"] = aluno.nome
                
            # Incluir status se não estiver incluído
            if "status" not in resposta_filtrada:
                resposta_filtrada["status"] = resposta_completa["status"]
                
            return resposta_filtrada
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
                try:
                    aluno = Aluno.objects.filter(matricula=str(matricula)).first()
                    if not aluno:
                        logger.warning(f"Aluno não encontrado com matrícula: {matricula}")
                        return {"error": "Aluno não encontrado com a matrícula informada"}
                except Exception as e:
                    logger.error(f"Erro ao buscar por matrícula {matricula}: {str(e)}")
                    return {"error": f"Erro ao buscar por matrícula: {str(e)}"}
            elif student_id:
                try:
                    aluno = Aluno.objects.filter(id=student_id).first()
                    if not aluno:
                        logger.warning(f"Aluno não encontrado com ID: {student_id}")
                        return {"error": "Aluno não encontrado pelo ID"}
                except Exception as e:
                    logger.error(f"Erro ao buscar por ID {student_id}: {str(e)}")
                    return {"error": f"Erro ao buscar por ID: {str(e)}"}
            elif name:
                # Verificar se o nome é válido
                if not name or not isinstance(name, str):
                    logger.error(f"Nome inválido fornecido para busca: {name}")
                    return {"error": "Nome inválido fornecido para busca"}
                
                logger.info(f"Buscando alunos com nome: '{name}'")
                try:
                    alunos = list(Aluno.objects.filter(nome__icontains=name))
                    logger.info(f"Busca encontrou {len(alunos)} alunos")
                    
                    # Verificar o tipo de cada objeto retornado
                    for i, a in enumerate(alunos):
                        logger.info(f"Aluno {i+1}: tipo={type(a)}, repr={repr(a)}")
                        
                    if len(alunos) == 1:
                        aluno = alunos[0]
                        logger.info(f"Selecionando único aluno: tipo={type(aluno)}, repr={repr(aluno)}")
                        # Verificar se o objeto aluno é válido
                        if not isinstance(aluno, Aluno):
                            logger.error(f"Objeto retornado não é um Aluno: {type(aluno)}")
                            return {"error": f"Erro interno: objeto retornado não é um Aluno"}
                    elif len(alunos) > 1:
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
                    else:
                        logger.warning(f"Nenhum aluno encontrado com o nome: {name}")
                        return {"error": f"Nenhum aluno encontrado com o nome: {name}"}
                except Exception as e:
                    logger.error(f"Erro durante a busca de alunos: {str(e)}")
                    return {"error": f"Erro durante a busca de alunos: {str(e)}"}
            
            if not aluno:
                return {"error": "Aluno não encontrado"}
            
            # Verificação adicional para garantir que aluno não seja None ou um tipo não esperado
            if isinstance(aluno, str):
                logger.error(f"Objeto aluno é uma string: {aluno}")
                return {"error": f"Erro interno: o objeto aluno é uma string, não um objeto Aluno"}
            elif not isinstance(aluno, Aluno):
                logger.error(f"Objeto aluno é do tipo inesperado: {type(aluno)}")
                return {"error": f"Erro interno: o objeto aluno é do tipo {type(aluno)}, não do tipo Aluno"}
            
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
                disciplina = nota.disciplina if hasattr(nota, 'disciplina') and nota.disciplina else "Sem disciplina"
                if isinstance(disciplina, str):
                    disciplina_nome = disciplina
                else:
                    disciplina_nome = disciplina.nome if hasattr(disciplina, 'nome') else str(disciplina)
                
                if disciplina_nome not in notas_por_disciplina:
                    notas_por_disciplina[disciplina_nome] = []
                
                notas_por_disciplina[disciplina_nome].append({
                    "valor": nota.valor,
                    "data": nota.data.strftime('%d/%m/%Y') if hasattr(nota, 'data') and nota.data else None,
                    "descricao": nota.descricao if hasattr(nota, 'descricao') else None
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
                try:
                    aluno = Aluno.objects.filter(matricula=str(matricula)).first()
                    if not aluno:
                        logger.warning(f"Aluno não encontrado com matrícula: {matricula}")
                        return {"error": "Aluno não encontrado com a matrícula informada"}
                except Exception as e:
                    logger.error(f"Erro ao buscar por matrícula {matricula}: {str(e)}")
                    return {"error": f"Erro ao buscar por matrícula: {str(e)}"}
            elif student_id:
                try:
                    aluno = Aluno.objects.filter(id=student_id).first()
                    if not aluno:
                        logger.warning(f"Aluno não encontrado com ID: {student_id}")
                        return {"error": "Aluno não encontrado pelo ID"}
                except Exception as e:
                    logger.error(f"Erro ao buscar por ID {student_id}: {str(e)}")
                    return {"error": f"Erro ao buscar por ID: {str(e)}"}
            elif name:
                # Verificar se o nome é válido
                if not name or not isinstance(name, str):
                    logger.error(f"Nome inválido fornecido para busca: {name}")
                    return {"error": "Nome inválido fornecido para busca"}
                
                logger.info(f"Buscando alunos com nome: '{name}'")
                try:
                    alunos = list(Aluno.objects.filter(nome__icontains=name))
                    logger.info(f"Busca encontrou {len(alunos)} alunos")
                    
                    # Verificar o tipo de cada objeto retornado
                    for i, a in enumerate(alunos):
                        logger.info(f"Aluno {i+1}: tipo={type(a)}, repr={repr(a)}")
                        
                    if len(alunos) == 1:
                        aluno = alunos[0]
                        logger.info(f"Selecionando único aluno: tipo={type(aluno)}, repr={repr(aluno)}")
                        # Verificar se o objeto aluno é válido
                        if not isinstance(aluno, Aluno):
                            logger.error(f"Objeto retornado não é um Aluno: {type(aluno)}")
                            return {"error": f"Erro interno: objeto retornado não é um Aluno"}
                    elif len(alunos) > 1:
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
                    else:
                        logger.warning(f"Nenhum aluno encontrado com o nome: {name}")
                        return {"error": f"Nenhum aluno encontrado com o nome: {name}"}
                except Exception as e:
                    logger.error(f"Erro durante a busca de alunos: {str(e)}")
                    return {"error": f"Erro durante a busca de alunos: {str(e)}"}
            
            if not aluno:
                return {"error": "Aluno não encontrado"}
            
            # Verificação adicional para garantir que aluno não seja None ou um tipo não esperado
            if isinstance(aluno, str):
                logger.error(f"Objeto aluno é uma string: {aluno}")
                return {"error": f"Erro interno: o objeto aluno é uma string, não um objeto Aluno"}
            elif not isinstance(aluno, Aluno):
                logger.error(f"Objeto aluno é do tipo inesperado: {type(aluno)}")
                return {"error": f"Erro interno: o objeto aluno é do tipo {type(aluno)}, não do tipo Aluno"}
            
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
                disciplina = nota.disciplina if hasattr(nota, 'disciplina') and nota.disciplina else "Sem disciplina"
                if isinstance(disciplina, str):
                    disciplina_nome = disciplina
                else:
                    disciplina_nome = disciplina.nome if hasattr(disciplina, 'nome') else str(disciplina)
                
                if disciplina_nome not in medias_por_disciplina:
                    medias_por_disciplina[disciplina_nome] = {"soma": 0, "count": 0}
                
                medias_por_disciplina[disciplina_nome]["soma"] += nota.valor
                medias_por_disciplina[disciplina_nome]["count"] += 1
            
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
            if hasattr(aluno, 'turma') and aluno.turma:
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
    
    def cross_reference_data(self, query_type, params=None):
        """
        Realiza consultas complexas que exigem cruzamento de dados de alunos.
        
        Args:
            query_type: Tipo de consulta a ser realizada (ex: 'alunos_por_turma', 'comparacao_desempenho', etc.)
            params: Parâmetros adicionais para a consulta (ex: turma, ano, etc.)
            
        Returns:
            Dicionário com os resultados da consulta
        """
        try:
            if not params:
                params = {}
                
            logger.info(f"Realizando consulta complexa do tipo: {query_type} com parâmetros: {params}")
            
            # Consulta de alunos por turma
            if query_type == "alunos_por_turma":
                turma = params.get("turma")
                if not turma:
                    return {"error": "É necessário informar a turma para esta consulta"}
                
                alunos = Aluno.objects.filter(turma=turma, ativo=True)
                if not alunos.exists():
                    return {"error": f"Não foram encontrados alunos na turma {turma}"}
                
                alunos_list = []
                for aluno in alunos:
                    alunos_list.append({
                        "id": aluno.id,
                        "nome": aluno.nome,
                        "matricula": aluno.matricula
                    })
                
                return {
                    "turma": turma,
                    "total_alunos": len(alunos_list),
                    "alunos": alunos_list
                }
            
            # Comparação de desempenho entre alunos
            elif query_type == "comparacao_desempenho":
                aluno1_id = params.get("aluno1_id")
                aluno2_id = params.get("aluno2_id")
                
                if not aluno1_id or not aluno2_id:
                    return {"error": "É necessário informar os IDs dos dois alunos para comparação"}
                
                # Obter dados do primeiro aluno
                aluno1 = Aluno.objects.filter(id=aluno1_id).first()
                if not aluno1:
                    return {"error": f"Aluno com ID {aluno1_id} não encontrado"}
                
                # Obter dados do segundo aluno
                aluno2 = Aluno.objects.filter(id=aluno2_id).first()
                if not aluno2:
                    return {"error": f"Aluno com ID {aluno2_id} não encontrado"}
                
                # Obter notas dos alunos
                notas_aluno1 = Nota.objects.filter(aluno=aluno1)
                notas_aluno2 = Nota.objects.filter(aluno=aluno2)
                
                # Calcular médias
                media_aluno1 = notas_aluno1.aggregate(media=Avg('valor'))['media'] or 0
                media_aluno2 = notas_aluno2.aggregate(media=Avg('valor'))['media'] or 0
                
                # Formatar resultado
                return {
                    "comparacao": {
                        "aluno1": {
                            "id": aluno1.id,
                            "nome": aluno1.nome,
                            "media": round(media_aluno1, 2)
                        },
                        "aluno2": {
                            "id": aluno2.id,
                            "nome": aluno2.nome,
                            "media": round(media_aluno2, 2)
                        },
                        "diferenca": round(abs(media_aluno1 - media_aluno2), 2),
                        "melhor_desempenho": aluno1.nome if media_aluno1 > media_aluno2 else 
                                            aluno2.nome if media_aluno2 > media_aluno1 else "Empate"
                    }
                }
            
            # Ranking de alunos por média
            elif query_type == "ranking_alunos":
                turma = params.get("turma")
                limite = params.get("limite", 10)  # Padrão: top 10
                
                # Filtro base
                query = {}
                if turma:
                    query["aluno__turma"] = turma
                
                # Obter notas e calcular médias por aluno
                alunos_medias = {}
                notas = Nota.objects.filter(**query)
                
                for nota in notas:
                    aluno_id = nota.aluno.id
                    if aluno_id not in alunos_medias:
                        alunos_medias[aluno_id] = {
                            "nome": nota.aluno.nome,
                            "notas": [],
                            "total": 0,
                            "count": 0
                        }
                    
                    alunos_medias[aluno_id]["notas"].append(nota.valor)
                    alunos_medias[aluno_id]["total"] += nota.valor
                    alunos_medias[aluno_id]["count"] += 1
                
                # Calcular médias e criar ranking
                ranking = []
                for aluno_id, dados in alunos_medias.items():
                    if dados["count"] > 0:
                        media = dados["total"] / dados["count"]
                        ranking.append({
                            "id": aluno_id,
                            "nome": dados["nome"],
                            "media": round(media, 2)
                        })
                
                # Ordenar por média (decrescente)
                ranking.sort(key=lambda x: x["media"], reverse=True)
                
                # Limitar ao número solicitado
                ranking = ranking[:limite]
                
                return {
                    "ranking": ranking,
                    "total_alunos": len(ranking),
                    "turma": turma if turma else "Todas as turmas"
                }
            
            # Estatísticas gerais da turma
            elif query_type == "estatisticas_turma":
                turma = params.get("turma")
                if not turma:
                    return {"error": "É necessário informar a turma para esta consulta"}
                
                # Contar alunos na turma
                total_alunos = Aluno.objects.filter(turma=turma, ativo=True).count()
                
                # Obter estatísticas de notas
                notas_query = Nota.objects.filter(aluno__turma=turma)
                estatisticas_notas = notas_query.aggregate(
                    media=Avg('valor'),
                    maxima=Max('valor'),
                    minima=Min('valor')
                )
                
                # Calcular distribuição por faixas
                notas_list = list(notas_query.values_list('valor', flat=True))
                
                faixas = {
                    "0-2.9": 0,
                    "3-4.9": 0,
                    "5-6.9": 0,
                    "7-8.9": 0,
                    "9-10": 0
                }
                
                for nota in notas_list:
                    if nota < 3:
                        faixas["0-2.9"] += 1
                    elif nota < 5:
                        faixas["3-4.9"] += 1
                    elif nota < 7:
                        faixas["5-6.9"] += 1
                    elif nota < 9:
                        faixas["7-8.9"] += 1
                    else:
                        faixas["9-10"] += 1
                
                # Calcular percentuais
                total_notas = len(notas_list)
                distribuicao = {}
                if total_notas > 0:
                    for faixa, quantidade in faixas.items():
                        distribuicao[faixa] = {
                            "quantidade": quantidade,
                            "percentual": round((quantidade / total_notas) * 100, 2)
                        }
                
                return {
                    "turma": turma,
                    "total_alunos": total_alunos,
                    "estatisticas_notas": {
                        "media": round(estatisticas_notas["media"] or 0, 2),
                        "maxima": estatisticas_notas["maxima"] or 0,
                        "minima": estatisticas_notas["minima"] or 0,
                        "total_notas": total_notas
                    },
                    "distribuicao_notas": distribuicao
                }
            
            else:
                return {"error": f"Tipo de consulta não suportado: {query_type}"}
                
        except Exception as e:
            logger.error(f"Erro ao realizar consulta complexa: {str(e)}")
            return {"error": f"Erro ao realizar consulta: {str(e)}"}
