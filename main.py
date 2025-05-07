import pandas as pd
import streamlit as st
from fpdf import FPDF
from io import BytesIO
import datetime
import locale


# Configurações de estilo
st.set_page_config(
    page_title="Gerador de Orçamentos SEDA",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .fixed-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
        background: #0068c9;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border: none;
        font-weight: bold;
    }
    
    .fixed-button:hover {
        background: #0052a3;
        color: white !important;
    }
    
    .item-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do estado da sessão
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'cliente': {
            'nome': '',
            'empresa': '',
            'referencia': '',
            'telefone': '',
            'email': '',
            'local': ''
        },
        'objeto_proposta': 'Manutenção em um banco regulador de tensão de 15 KV.',
        'itens': [],
        'servico_manual': False,
        'ultimo_item': 0
    }

# Funções auxiliares
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def quebrar_texto(pdf, texto, largura_max):
    palavras = texto.split()
    linhas = []
    linha_atual = ''
    
    for palavra in palavras:
        if pdf.get_string_width(linha_atual + ' ' + palavra) < largura_max - 5:  # Margem de segurança
            linha_atual += ' ' + palavra if linha_atual else palavra
        else:
            if pdf.get_string_width(palavra) > largura_max:  # Quebra palavra longa
                parte = ''
                for letra in palavra:
                    if pdf.get_string_width(parte + letra) < largura_max - 5:
                        parte += letra
                    else:
                        linhas.append(parte + '-')
                        parte = letra
                linhas.append(parte)
            else:
                linhas.append(linha_atual)
                linha_atual = palavra
    linhas.append(linha_atual)
    return linhas

# Interface principal
st.title("📝 Gerador de Orçamentos SEDA")

# Seção de informações do cliente
with st.expander("📋 Informações do Cliente", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.dados['cliente']['nome'] = st.text_input(
            "Nome do Contato*",
            value=st.session_state.dados['cliente']['nome']
        )
        st.session_state.dados['cliente']['empresa'] = st.text_input(
            "Empresa*",
            value=st.session_state.dados['cliente']['empresa']
        )
        st.session_state.dados['cliente']['referencia'] = st.text_input(
            "Referente a*",
            value=st.session_state.dados['cliente']['referencia']
        )
    
    with col2:
        st.session_state.dados['cliente']['telefone'] = st.text_input(
            "Telefone*",
            value=st.session_state.dados['cliente']['telefone']
        )
        st.session_state.dados['cliente']['email'] = st.text_input(
            "E-mail",
            value=st.session_state.dados['cliente']['email']
        )
        st.session_state.dados['cliente']['local'] = st.text_input(
            "Local da Obra*",
            value=st.session_state.dados['cliente']['local']
        )

# Objeto da proposta
st.session_state.dados['objeto_proposta'] = st.text_area(
    "✏️ Objeto da Proposta*",
    value=st.session_state.dados['objeto_proposta'],
    height=100
)

# Seção de serviços
st.divider()
st.subheader("➕ Adicionar Serviços")

use_manual = st.checkbox("Adicionar serviço manualmente")
servico = ''
descricao = ''
preco = 0.0

if use_manual:
    col1, col2 = st.columns(2)
    with col1:
        servico = st.text_input("Nome do Serviço*", key='servico_manual')
        descricao = st.text_area("Descrição Detalhada*", key='desc_manual')
    with col2:
        preco = st.number_input("Valor Unitário*", min_value=0.0, step=50.0, key='preco_manual')
else:
    @st.cache_data
    def carregar_servicos():
        return pd.read_csv("servicos.csv")
    
    df = carregar_servicos()
    servico_selecionado = st.selectbox(
        "Selecione o Serviço",
        df['nome'],
        index=None
    )
    
    if servico_selecionado:
        dados = df[df['nome'] == servico_selecionado].iloc[0]
        servico = dados['nome']
        descricao = dados['descricao']
        preco = dados['preco_unitario']

quantidade = st.number_input("Quantidade*", min_value=1, value=1, key='quantidade')

if st.button("Adicionar Serviço") and servico and descricao and preco > 0:
    st.session_state.dados['ultimo_item'] += 1
    novo_item = {
        'item': st.session_state.dados['ultimo_item'],
        'servico': servico,
        'descricao': descricao,
        'quantidade': quantidade,
        'preco_unitario': preco,
        'total': preco * quantidade
    }
    
    st.session_state.dados['itens'].append(novo_item)
    
    # Limpar campos manuais
    if use_manual:
        st.session_state.dados['servico_manual'] = False
        st.session_state.dados['servico_manual'] = ''
        st.session_state.dados['desc_manual'] = ''
        st.session_state.dados['preco_manual'] = 0.0
    
    st.rerun()

# Lista de itens adicionados
if st.session_state.dados['itens']:
    st.divider()
    st.subheader("📦 Itens do Orçamento")
    
    for idx, item in enumerate(st.session_state.dados['itens']):
        with st.container():
            st.markdown(f"<div class='item-card'>", unsafe_allow_html=True)
            
            cols = st.columns([1, 3, 1, 1, 1, 0.5])
            cols[0].markdown(f"**Item {item['item']}**")
            cols[1].markdown(f"**{item['servico']}**")
            cols[1].caption(item['descricao'])
            cols[2].markdown(f"**Qtd:** {item['quantidade']}")
            cols[3].markdown(f"**Unitário:** {formatar_moeda(item['preco_unitario'])}")
            cols[4].markdown(f"**Total:** {formatar_moeda(item['total'])}")
            
            if cols[5].button("❌", key=f"del_{idx}"):
                del st.session_state.dados['itens'][idx]
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

# Classe PDF com formatação corrigida
class PDF(FPDF):
    def header(self):
        self.image("fundo.jpg", 0, 0, self.w, self.h)
    
    def footer(self):
        pass
    
    def criar_tabela_informacoes(self):
        # Configurações de posição
        x = 10
        y = 170
        largura = 180
        altura = 60

        # Dados dinâmicos
        cliente = st.session_state.dados['cliente']
        data = datetime.datetime.now().strftime('%d/%m/%Y')
        
        # Textos organizados
        conteudo = [
            "DEPARTAMENTO TÉCNICO\n"
            "Email: delzioav@yahoo.com.br\n"
            "Tel: (31) 98229.9162\n\n"
            "DELZIO DE AVELAR - COMERCIAL\n"
            "Email: delzioseda@gmail.com\n"
            "Fone: 31-98229.9162",
            
            f"PARA: {cliente['empresa']}\n"
            f"REF: {cliente['referencia']}\n"
            "",
            
            f"\n\nData: {data}\n"
            "Validade da proposta: 10 dias",
            
            f"A/C: {cliente['nome']}\n"
            f"Contato: {cliente['telefone']}\n"
            f"Email: {cliente['email']}\n"
            f"Local: {cliente['local']}"
        ]

        # Configurar estilo
        self.set_font('helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(150, 150, 150)

        # Desenhar contorno externo
        self.rect(x, y, largura, altura)
        
        # Desenhar divisória vertical central
        self.line(
            x + largura/2, y,
            x + largura/2, y + altura
        )

        # Adicionar textos
        positions = [
            (x + 5, y + 5),          # Célula 1 (esquerda superior)
            (x + largura/2 + 5, y + 5),  # Célula 2 (direita superior)
            (x + 5, y + altura/2 + 5),   # Célula 3 (esquerda inferior)
            (x + largura/2 + 5, y + altura/2 + 5)  # Célula 4 (direita inferior)
        ]

        for i, (pos_x, pos_y) in enumerate(positions):
            self.set_xy(pos_x, pos_y)
            self.multi_cell(largura/2 - 10, 5, conteudo[i], align='L')
    
    
def gerar_pdf():
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(20, 55, 20)
        
        # --- Página 1 - Cabeçalho ---
        pdf.set_font("helvetica", 'B', 12)
        
        pdf.criar_tabela_informacoes()

        # --- Página 2 - Conteúdo Principal ---
        pdf.add_page()
        
        
        # Número da proposta
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, f"PROPOSTA TÉCNICA E COMERCIAL: 00109/{datetime.datetime.now().year}", ln=1)
        pdf.ln(2)

        # Introdução
        pdf.set_font("helvetica", size=10)
        intro_texto = """Honrados pela oportunidade de apresentarmos nossos serviços, vimos por esta apresentar-lhes a
nossa Proposta Técnica para o fornecimento em questão.

Antecipadamente agradecemos e colocamo-nos ao seu dispor para quaisquer esclarecimentos
adicionais."""
        
        # Ajuste nas configurações do texto
        largura_util = 170  # Largura máxima considerando margens de 20mm

        # Texto introdutório
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(largura_util, 6, intro_texto)
        pdf.ln(5)

        # Objeto da Proposta
        pdf.set_font("helvetica", 'B', 11)
        pdf.cell(largura_util, 10, "1. OBJETO DA PROPOSTA:", ln=1)
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(
            largura_util,  # Largura controlada
            6,  # Altura da linha
            st.session_state.dados['objeto_proposta'],
            0,  # Borda (0 = sem borda)
            'J'  # Alinhamento justificado
        )
        pdf.ln(1)

        # Itens Excluídos
        pdf.set_font("helvetica", 'B', 11)
        pdf.cell(0, 10, "Consideramos fora do nosso escopo de fornecimento os seguintes itens:", ln=1)
        exclusoes = [
            "Fornecimento de água potável no local da obra.",
            "Fornecimento de energia elétrica no local da obra.",
            "Instalações sanitárias no local da obra.",
            "Local para armazenamento de materiais e ferramentas.",
            "Qualquer outra atividade e materiais não incluída no objeto da proposta.",
            "Obras externas Cemig (Ramal de ligação, religador, extensão de rede, etc)",
            "Fornecimento de gerador",
            "Transporte do equipamento"
        ]
        
        pdf.set_font("helvetica", size=10)
        for item in exclusoes:
            pdf.cell(3, 6, "> ")
            pdf.multi_cell(0, 6, item)
            pdf.set_x(20)
        
        # Tabela de Itens
        pdf.ln(5)
        col_widths = [12, 15, 75, 30, 30]
        y_pos = pdf.get_y()
        
        # Cabeçalho da Tabela
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font("helvetica", 'B', 10)
        for i, header in enumerate(["ITEM", "QUANT", "DESCRIÇÃO", "VALOR UNITÁRIO", "TOTAL"]):
            pdf.set_xy(20 + sum(col_widths[:i]), y_pos)
            pdf.cell(col_widths[i], 10, header, 1, 0, 'C', 1)
        
        y_pos += 10

        # Linhas dos Itens
        pdf.set_font("helvetica", size=9)
        for item in st.session_state.dados['itens']:
            if y_pos > 250:  # Quebra de página
                pdf.add_page()
                y_pos = 40
            
            # Quebra de texto
            desc_lines = quebrar_texto(pdf, item['descricao'], col_widths[2])
            line_count = len(desc_lines)
            row_height = 5 * line_count

            # Desenhar células
            pdf.set_xy(20, y_pos)
            
            # Item
            pdf.multi_cell(col_widths[0], row_height, str(item['item']), 1, 'C')
            
            # Quantidade
            pdf.set_xy(20 + col_widths[0], y_pos)
            pdf.multi_cell(col_widths[1], row_height, str(item['quantidade']), 1, 'C')
            
            # Descrição
            pdf.set_xy(20 + col_widths[0] + col_widths[1], y_pos)
            for line in desc_lines:
                pdf.cell(col_widths[2], 5, line, 1, 0, 'L')
                pdf.ln(5)
                pdf.set_x(20 + col_widths[0] + col_widths[1])
            
            # Valores
            pdf.set_xy(20 + sum(col_widths[:3]), y_pos)
            pdf.multi_cell(col_widths[3], row_height, formatar_moeda(item['preco_unitario']), 1, 'R')
            
            pdf.set_xy(20 + sum(col_widths[:4]), y_pos)
            pdf.multi_cell(col_widths[4], row_height, formatar_moeda(item['total']), 1, 'R')
            
            y_pos += row_height

        # Total Geral
        pdf.set_fill_color(200, 200, 200)
        pdf.set_xy(20, y_pos)
        pdf.cell(sum(col_widths[:3]), 10, "TOTAL:", 1, 0, 'L', 1)
        pdf.cell(col_widths[3], 10, "", 1, 0, 'C', 1)
        total_geral = sum(item['total'] for item in st.session_state.dados['itens'])
        pdf.cell(col_widths[4], 10, formatar_moeda(total_geral), 1, 0, 'R', 1)

        

        # --- Página 3 - Finalização ---
        pdf.add_page()
        pdf.set_xy(20, 60)
        
        # Condições de Pagamento
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(0, 10, "CONDIÇÕES DE PAGAMENTO: Na entrega do serviço", ln=1)
        
        # Texto Final
        pdf.set_font("helvetica", size=10)
        texto_final = """Desde já, agradecemos o seu contato e permanecemos à disposição para maiores
informações. Cordialmente,"""
        pdf.multi_cell(0, 6, texto_final)
        
        # Assinatura
        pdf.set_xy(20, 200)

        # Linha de assinatura (100mm de comprimento)
        pdf.line(20, 200, 80, 200)  # x1, y1, x2, y2

        # Nome
        pdf.set_xy(20, 205)  # 5mm abaixo da linha
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 6, "Délzio de Avelar", ln=1)  # Altura reduzida para 6mm

        # CNPJ
        pdf.set_x(20)
        pdf.set_font("helvetica", size=10)
        pdf.cell(0, 5, "12.045.144/0001-43", ln=1)  # Altura 5mm

        # Geração do PDF
        buffer = BytesIO()
        pdf.output(buffer)
        return buffer.getvalue()

    except Exception as e:
        st.error(f"Erro na geração do PDF: {str(e)}")
        raise
# Botão fixo de geração de PDF
if st.session_state.dados['itens']:
    st.markdown("""
    <div class="fixed-button">
        <style>
            .stDownloadButton>button {
                background: #0068c9 !important;
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("📄 GERAR PDF FINAL", key='fixed_pdf_button'):
        try:
            pdf_bytes = gerar_pdf()
            st.download_button(
                label="⬇️ BAIXAR ORÇAMENTO PRONTO",
                data=pdf_bytes,
                file_name=f"Proposta_SEDA_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Falha na geração do PDF: {str(e)}")
    