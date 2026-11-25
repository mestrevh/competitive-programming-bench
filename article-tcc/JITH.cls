%%~~~~~~~~~~~~~~~~~~~~~~~
%%~~~~~~~~~~~~~~~~~~~~~~~
%%Padrao JITH 
%%~~~~~~~~~~~~~~~~~~~~~~~
%%~~~~~~~~~~~~~~~~~~~~~~~
%%(1) Inclua os detalhes em "Identificacao.tex".
%%(2) Escreva os capitulos nas pastas apropriadas.
%%(3) Chame os arquivos em "main.tex"
%%(4) Adicione quantas pastas for necessario.
%%~~~~~~~~~~~~~~~~~~~~~~~
%%~~~~~~~~~~~~~~~~~~~~~~~
\NeedsTeXFormat{LaTeX2e} %[2016/04/20]
\ProvidesClass{JITH}[2019/10/24 v4.5  JITH LaTeX document class]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ExecuteOptions{12pt}
\ProcessOptions
\LoadClass{report}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%% OTHER PACKAGES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\RequirePackage{fancyhdr}
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{setspace}
\RequirePackage{xifthen}
\RequirePackage[svgnames,dvipsnames]{xcolor}
\RequirePackage[brazilian]{babel}
\RequirePackage[top=3cm,bottom=2cm,right=2cm,left=3cm]{geometry}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%% TITLE PAGES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\def\@university{Universidade Federal de Alagoas}
\def\docTitle#1{\gdef\@docTitle{#1}}
\def\author#1{\gdef\@author{#1}}
% e-mail institucional do autor, impresso em fonte monoespaçada abaixo do nome na capa (vazio = omitido)
\def\email#1{\gdef\@email{#1}}
\gdef\@email{}
\def\@department{Instituto de Computação}
\def\docType#1{\gdef\@docType{#1}}
\def\orientador#1{\gdef\@orientador{#1}}
\def\tituloOrientador#1{\gdef\@tituloOrientador{#1}}
\def\coorientador#1{\gdef\@coorientador{#1}}
\def\tituloCoorientador#1{\gdef\@tituloCoorientador{#1}}
%
\def\memberA#1{\gdef\@memberA{#1}}
\def\memberB#1{\gdef\@memberB{#1}}
\def\memberC#1{\gdef\@memberC{#1}}
\def\memberD#1{\gdef\@memberD{#1}}
\def\memberE#1{\gdef\@memberE{#1}}
\def\filiationA#1{\gdef\@filiationA{#1}}
\def\filiationB#1{\gdef\@filiationB{#1}}
\def\filiationC#1{\gdef\@filiationC{#1}}
\def\filiationD#1{\gdef\@filiationD{#1}}
\def\filiationE#1{\gdef\@filiationE{#1}}
% valores padrão vazios (campos opcionais testados na folha de rosto e na de aprovação)
\def\@memberA{}\def\@memberB{}\def\@memberC{}\def\@memberD{}\def\@memberE{}
\def\@filiationD{}\def\@filiationE{}\def\@coorientador{}\def\@tituloCoorientador{}
%
\def\setDate#1{\gdef\@setDate{#1}}
\def\setMonth#1{\gdef\@setMonth{#1}}
\def\setYear#1{\gdef\@setYear{#1}}
\def\setLocation#1{\gdef\@setLocation{#1}}

\newcommand{\myifnotempty}[2]{\ifthenelse{\not\equal{#1}{}}{#2}{}}
% data por extenso; sem dia (\setDate{}), imprime só mês e ano
\newcommand{\@dataExtenso}{\ifthenelse{\equal{\@setDate}{}}{\@setMonth~de~\@setYear}{\@setDate~de~\@setMonth~de~\@setYear}}

% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\capa{%
\pagenumbering{roman}
	\thispagestyle{empty}
	
	\begin{minipage}{1\textwidth}
		\raggedleft \includegraphics[height=35mm]{Cap00/logo_ic.png}
	\end{minipage}

	\vfill

    \hspace{-1.5cm}\begin{minipage}{1\textwidth}
		\raggedright \large\textit{{
		    \ifthenelse{\@docType=1}{Trabalho de Conclusão de Curso}{
		    \ifthenelse{\@docType=2}{Proposta de Dissertação de Mestrado}{
		    \ifthenelse{\@docType=3}{Dissertação de Mestrado}{
		    \ifthenelse{\@docType=4}{Qualificação de Doutorado}{
		    \ifthenelse{\@docType=4}{Tese de Doutorado}{
		    E R R O R}}}}}}}
	\end{minipage}
	
	\vspace{5mm}
	
    \hspace{-1.5cm}\scalebox{1.35}{\begin{minipage}{.7\textwidth}
    \renewcommand{\baselinestretch}{0.95}\raggedright\LARGE{\textbf\@docTitle}\\
    \end{minipage}}
    
    \vspace{1cm}

    \hspace{-1.0cm}\scalebox{1}{\begin{minipage}{1\textwidth}
		\renewcommand{\baselinestretch}{1}\raggedright {\textbf{\large\@author}}\myifnotempty{\@email}{\\[2pt]{\ttfamily\@email}}
	\end{minipage}}

    \vspace{1cm}

    \hspace{-1.0cm}\scalebox{1}{\begin{minipage}{1\textwidth}
		\renewcommand{\baselinestretch}{1}\raggedright {\textbf{orientado por}}\\
		\large {\textbf{\@tituloOrientador~\@orientador}}
		%\myifnotempty{\@coorientador}{\\ \textbf{\@tituloCoorientador~\@coorientador}}
	\end{minipage}}
	
	\vspace{1cm}
	
	\definecolor{icbackcolor}{RGB}{ 0, 74, 172}
	\definecolor{icfrontcolor}{RGB}{203, 208, 227}
\hfill\fcolorbox{icfrontcolor}{icfrontcolor}{\begin{minipage}[r][2.5cm]{0.6\textwidth}
				\renewcommand{\baselinestretch}{1}\raggedleft\large\@university\\
				\@department\\
				\@setLocation\\
				\@dataExtenso
			\end{minipage}}\fcolorbox{icbackcolor}{icbackcolor}{\begin{minipage}[r][2.5cm]{8mm}   \hspace{8mm}\end{minipage}}\hspace{-2cm}
	
	\thispagestyle{empty}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
	
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\renewcommand{\baselinestretch}{1.5} 
\def\folhaDeRosto{%
	\thispagestyle{empty}
	
	\begin{center}
\thispagestyle{empty}
{\MakeUppercase\@university}\\
{\@department}

\vfill	

{\textbf{\large\MakeUppercase\@docTitle}}

\vspace{2cm}

\hspace{.45\textwidth}
\begin{minipage}{.5\textwidth}
	{\ifthenelse{\@docType=1}{Trabalho de Conclusão de Curso}{
	 \ifthenelse{\@docType=2}{Proposta de Dissertação de Mestrado submetida}{
	 \ifthenelse{\@docType=3}{Dissertação de Mestrado submetida}{
	 \ifthenelse{\@docType=4}{Qualificação de Doutorado submetida}{
	 \ifthenelse{\@docType=5}{Tese de Doutorado submetida}{
	 E R R O R}}}}}}
	apresentado ao {\@department} da {\@university} como requisito parcial para a obtenção do grau de   {\ifthenelse{\@docType=1}{Bacharel em \mbox{Ciência} da Computação}{
	 \ifthenelse{\@docType=2}{Mestre em Informática}{
	 \ifthenelse{\@docType=3}{Mestre em Informática}{
	 \ifthenelse{\@docType=4}{Doutor em Informática}{
	 \ifthenelse{\@docType=5}{Doutor em Informática}{
	 E R R O R}}}}}}.
\end{minipage}%

\vspace*{\fill}

{\large\@author}\vspace{1cm}

{\textit{\textbf{Orientador: \@tituloOrientador~\@orientador}}}

%\myifnotempty{\@coorientador}{\textit{\textbf{Co-advisor: \@tituloCoorientador~\@coorientador}}}

\vspace{1cm}

\myifnotempty{\@memberA\@memberB\@memberC\@memberD\@memberE}{%
\textbf{Banca Avaliadora:}

\vspace{5mm}
\begin{tabular}{lr}
\myifnotempty{\@memberA}{\@memberA&\@filiationA\\}
\myifnotempty{\@memberB}{\@memberB&\@filiationB\\}
\myifnotempty{\@memberC}{\@memberC&\@filiationC\\}
\myifnotempty{\@memberD}{\@memberD&\@filiationD\\}
\myifnotempty{\@memberE}{\@memberE&\@filiationE}
\end{tabular}}
\vfill

{\large\@setLocation}

{\large \@dataExtenso}

\end{center}
	
	\thispagestyle{empty}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\folhaDeAprovacao{%
	\thispagestyle{empty}

	\begin{center}
	{\MakeUppercase\@university}\\
	{\@department}
	
	\vfill	
	
	{\bfseries\large\MakeUppercase\@docTitle}
	
	\vspace{1cm}
	
	\vspace{5mm}
	
	%\hspace{.45\textwidth}
	\begin{minipage}{.8\textwidth}
		{\ifthenelse{\@docType=1}{Trabalho de Conclusão de Curso}{
	 \ifthenelse{\@docType=2}{Proposta de Dissertação de Mestrado submetida}{
	 \ifthenelse{\@docType=3}{Dissertação de Mestrado submetida}{
	 \ifthenelse{\@docType=4}{Qualificação de Doutorado submetida}{
	 \ifthenelse{\@docType=5}{Tese de Doutorado submetida}{
	 E R R O R}}}}}}
	apresentado ao {\@department} da {\@university} como requisito parcial para a obtenção do grau de   {\ifthenelse{\@docType=1}{Bacharel em \mbox{Ciência} da Computação}{
	 \ifthenelse{\@docType=2}{Mestre em Informática}{
	 \ifthenelse{\@docType=3}{Mestre em Informática}{
	 \ifthenelse{\@docType=4}{Doutor em Informática}{
	 \ifthenelse{\@docType=5}{Doutor em Informática}{
	 E R R O R}}}}}}.
	\end{minipage}%
	\vspace*{\fill}
	
	
	Aprovado em \@dataExtenso:
	
	\vspace{7mm}\vfill
	
%	\begin{minipage}{.8\textwidth}
%		\begin{center}
\myifnotempty{\@orientador}{
	\begin{tabular}{p{8cm}}
		\hline \centering\@orientador,\\ \@tituloOrientador, Orientador
	\end{tabular}\vspace{7mm}\vfill
}

\myifnotempty{\@coorientador}{
	\begin{tabular}{p{8cm}}
		\hline \centering\@coorientador,\\ \@tituloCoorientador, Co-orientador
	\end{tabular}\vspace{7mm}\vfill
}

\myifnotempty{\@memberA}{
	\begin{tabular}{p{8cm}}
		\hline \centering\@memberA,\\\@filiationA
	\end{tabular}\vspace{7mm}\vfill
}

\myifnotempty{\@memberB}{
	\begin{tabular}{p{8cm}}
		\hline \centering\@memberB,\\\@filiationB
	\end{tabular}\vspace{7mm}\vfill
}

\myifnotempty{\@memberC}{
	\begin{tabular}{p{8cm}}
		\hline \centering\@memberC,\\\@filiationC
	\end{tabular}\vspace{7mm}\vfill
}

\myifnotempty{\@memberD}{
	\begin{tabular}{p{8cm}}
		\hline \centering\@memberD,\\\@filiationD
	\end{tabular}\vspace{7mm}\vfill
}

\myifnotempty{\@memberE}{
	\begin{tabular}{p{8cm}}
		\hline \centering\@memberE,\\\@filiationE
	\end{tabular}\vfill
}
\end{center}

	\thispagestyle{empty}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\dedicatoria{%
    \thispagestyle{empty}
	\input{Cap00/Dedicatoria}
	\thispagestyle{empty}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\agradecimentos{%
    \thispagestyle{empty} 
	\input{Cap00/Agradecimentos}
	\thispagestyle{empty}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\epigrafe{%
    \thispagestyle{empty} 
	\input{Cap00/Epigrafe}
	\thispagestyle{empty}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\abstract{%
	\input{Cap00/Abstract}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\resumo{%
	\input{Cap00/Resumo}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\simbolos{%
	\input{Cap00/Simbolos}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\def\abreviaturas{%
	\input{Cap00/Abreviaturas}
	\clearpage{\thispagestyle{empty}\cleardoublepage}
}
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % %

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%% The End
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\endinput
%%
%% End of file `JITH.cls'.
