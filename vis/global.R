library(httr)

URL <- 'http://192.168.1.111:8000/inspectorbudget'

get_categories <- function(){

    r <- httr::GET(sprintf('%s/categories', URL), accept_json())
    request <- content(r, "parsed")
    request <- request[[4]]
    cat <- do.call(rbind, request)
    cat <- apply(cat, 2, unlist)
    return(as.data.frame(cat))
  }

CATEGORIES <- get_categories()$name

get_data <- function(){
    r <- httr::GET(sprintf('%s/entries/?limit=500000', URL), accept_json())
    request <- content(r, "parsed")
    request <- request[[4]]
    message(sprintf('There is %.0f entries.', length(request)))
    request <- lapply(request, function(x) as.data.frame(x, stringsAsFactors=FALSE))
    data <- do.call(rbind,request)

    year <- sapply(data$date, function(x) substr(x, 1, 4))
    month <- sapply(data$date, function(x) substr(x, 6, 7))
    data[, c("year", "month")] <- cbind(year, month)
    data$amount <- as.numeric(data$amount)

    cat <- get_categories()
    colnames(cat)[1] <- 'category'
    data <- merge(data, cat, by='category', how='left')
    data$category <- NULL
    data$x <- paste0(data$year, '-', data$month)
    return(data)
  }
                    
ButtonColumns <- function(df, id, ...) {
  # function to create one action button as string
  f <- function(i) {
    as.character(
        shiny::fluidRow(
            shiny::actionButton(
                as.character(i),
                label = NULL,
                icon = icon('trash'),
                onclick = 'Shiny.setInputValue(\"deletePressed\", this.id, {priority: "event"})'
            ),
            shiny::actionButton(
                paste0(as.character(i),2),
                label = NULL,
                icon = icon('pencil'),
                onclick = sprintf("window.open('%s/entries/%i', '_blank')", URL, i)
            )
        ))
  }

  deleteCol <- unlist(lapply(df$id, f))

  # Return a data table
  DT::datatable(cbind(df, options = deleteCol),
                # Need to disable escaping for html as string to work
                escape = FALSE,
                options = list(
                  # Disable sorting for the delete column
                  columnDefs = list(
                    list(targets = 8, sortable = FALSE)),
                  pageLength = 50
                ))
}