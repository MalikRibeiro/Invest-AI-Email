import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT
import os
import re

class ReportGenerator:
    def __init__(self):
        pass

    def generate_markdown_report(self, portfolio_df, total_value, suggestions_df, contribution_df, indicators, ai_analysis=None):
        today = datetime.now().strftime("%d/%m/%Y")
        
        # Resumo Executivo
        report = f"# 📊 Relatório Financeiro Diário - {today}\n\n"
        
        if ai_analysis:
            report += "## 🧠 Análise de IA\n"
            report += f"{ai_analysis}\n\n"
        else:
            report += "## 📝 Resumo Executivo\n"
            report += f"- **Valor Total da Carteira**: R$ {total_value:,.2f}\n"
            selic = indicators.get('selic_meta', 0)
            cdi = indicators.get('cdi', 0)
            ptax = indicators.get('ptax_venda', 0)
            report += f"- **Indicadores**: Selic {selic}% | CDI {cdi:.2f}% | PTAX R$ {ptax:.4f}\n\n"
        
        # Alocação Atual vs Ideal
        report += "## ⚖️ Alocação de Ativos\n"
        report += "| Categoria | Atual % | Ideal % | Status |\n"
        report += "|---|---|---|---|\n"
        
        for _, row in suggestions_df.iterrows():
            report += f"| {row['category']} | {row['current_pct']:.1f}% | {row['target_pct']:.1f}% | {row['status']} |\n"
            
        report += "\n"
        
        # Detalhe por Ativo
        report += "## 📈 Detalhe da Carteira\n"
        cats = portfolio_df['category'].unique()
        for cat in cats:
            cat_df = portfolio_df[portfolio_df['category'] == cat]
            report += f"### {cat}\n"
            report += "| Ativo | Qtd | Preço | Valor Total | Var. 1D | Var. 12M |\n"
            report += "|---|---|---|---|---|---|\n"
            for _, row in cat_df.iterrows():
                report += f"| {row['name']} ({row['ticker']}) | {row['qty']} | R$ {row['price']:,.2f} | R$ {row['value_brl']:,.2f} | {row['change_1d']:.2f}% | {row['change_12m']:.2f}% |\n"
            report += "\n"
            
        # Sugestão de Aporte
        report += "## 💰 Sugestão de Aporte Mensal (R$ 250,00)\n"
        if isinstance(contribution_df, str):
             report += f"{contribution_df}\n"
        else:
            report += "| Categoria | Valor Sugerido |\n"
            report += "|---|---|\n"
            for _, row in contribution_df.iterrows():
                report += f"| {row['category']} | R$ {row['contribution']:,.2f} |\n"
                
        return report

    def generate_pdf_report(self, portfolio_df, total_value, suggestions_df, contribution_df, indicators, ai_analysis=None, filename="daily_report.pdf"):
        """Generates a structured PDF report using ReportLab Platypus."""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom Styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.white,
            backColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=20,
            leading=30,
            borderPadding=10
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            textColor=colors.darkblue,
            spaceBefore=15,
            spaceAfter=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )

        today = datetime.now().strftime("%d/%m/%Y")
        
        # Title
        story.append(Paragraph(f"Relatório Financeiro Diário - {today}", title_style))
        story.append(Spacer(1, 12))
        
        # Summary / AI Analysis
        story.append(Paragraph("Análise de Desempenho", heading_style))
        
        # Highlight Total Value
        story.append(Paragraph(f"<b>Valor Total da Carteira: R$ {total_value:,.2f}</b>", 
                               ParagraphStyle('TotalValue', parent=styles['Normal'], fontSize=14, textColor=colors.darkgreen)))
        story.append(Spacer(1, 5))
        
        selic = indicators.get('selic_meta', 0)
        cdi = indicators.get('cdi', 0)
        ptax = indicators.get('ptax_venda', 0)
        story.append(Paragraph(f"Indicadores: Selic {selic}% | CDI {cdi:.2f}% | PTAX R$ {ptax:.4f}", styles['Normal']))
        story.append(Spacer(1, 10))

        if ai_analysis:
            # Clean up markdown bolding for PDF using Regex
            formatted_analysis = ai_analysis
            
            # 1. Escape special characters first (simple version)
            formatted_analysis = formatted_analysis.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # 2. Convert Markdown Headers to Bold
            formatted_analysis = re.sub(r'#+\s*(.*)', r'<b>\1</b>', formatted_analysis)
            
            # 3. Convert Markdown Bold (**text**) to HTML Bold (<b>text</b>)
            formatted_analysis = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_analysis)
            
            # Handle newlines
            for paragraph in formatted_analysis.split('\n'):
                if paragraph.strip():
                    story.append(Paragraph(paragraph, normal_style))
        else:
            story.append(Paragraph("Sem análise de IA disponível.", normal_style))
            
        story.append(Spacer(1, 12))
        
        # Allocation Table
        story.append(Paragraph("Alocação de Ativos", heading_style))
        data = [["Categoria", "Atual %", "Ideal %", "Status"]]
        for _, row in suggestions_df.iterrows():
            data.append([
                row['category'], 
                f"{row['current_pct']:.1f}%", 
                f"{row['target_pct']:.1f}%", 
                row['status']
            ])
            
        t = Table(data, colWidths=[150, 80, 80, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
        ]))
        story.append(t)
        story.append(Spacer(1, 12))
        
        # Contribution
        story.append(Paragraph("Sugestão de Aporte Mensal (R$ 250,00)", heading_style))
        if isinstance(contribution_df, str):
            story.append(Paragraph(contribution_df, normal_style))
        else:
            data = [["Categoria", "Valor Sugerido"]]
            for _, row in contribution_df.iterrows():
                data.append([row['category'], f"R$ {row['contribution']:,.2f}"])
            
            t = Table(data, colWidths=[200, 150])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
            ]))
            story.append(t)
            
        doc.build(story)
        return filename
