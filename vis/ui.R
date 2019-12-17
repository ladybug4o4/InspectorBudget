library(shinydashboard)
library(DT)
source('global.R')
cat <- get_categories()
CATEGORIES <- c(as.character(cat$name), '*')


dashboardPage(
  dashboardHeader(title='\U0001F575InspectorBudget'),
  dashboardSidebar(    
      sidebarMenu(
          menuItem("Dashboard", tabName = "dashboard", icon = icon("dashboard")),
          menuItem("Data", tabName = "data", icon = icon("th"))
    )),
  dashboardBody(
        tags$head(tags$style(
    HTML('.wrapper {height: auto !important; position:relative; overflow-x:hidden; overflow-y:hidden}')
  )),
      tabItems(
          tabItem(tabName = "dashboard", fluidRow(
              box(plotOutput("main", width="100%"), width=8),
              tabBox(
                  tabPanel("miesiące", tableOutput("stats"), width=3),
                  tabPanel("lata", tableOutput("stats2"), width=3),
                  width=3, height='422px'),
              box(
                  selectInput('cat', 'Wybierz kategorie:', CATEGORIES, c('Zakupy', 'Rachunki', 'Paliwo i transport'), multiple = TRUE),
                  plotOutput("categories", width="100%"),
                  radioButtons('type', '', c('Wydatki' ,'Przychody'), selected='Wydatki', inline=TRUE), width=11)
              )
          ),
          tabItem(tabName = "data", active=TRUE, fluidRow( box(dataTableOutput("data"), width=12) ) )
                 )
      )
)
