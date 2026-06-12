import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  InputAdornment,
  Chip,
  Grid,
  Skeleton,
  Tabs,
  Tab,
  Paper,
} from '@mui/material'
import { Search as SearchIcon, FilterList as FilterIcon } from '@mui/icons-material'
import { searchApi } from '../../api/client'

const Search = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [activeTab, setActiveTab] = useState(0)
  const [filters, setFilters] = useState({
    industry: '',
    domain: '',
    country: '',
    technology: '',
  })

  // Debounce search
  useState(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
    }, 500)
    return () => clearTimeout(timer)
  })

  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['search', debouncedQuery, activeTab, filters],
    queryFn: () => {
      const entityTypes = ['', 'company', 'product', 'service', 'news']
      return searchApi
        .search({
          q: debouncedQuery,
          entity_type: entityTypes[activeTab] || undefined,
          ...filters,
        })
        .then((res) => res.data)
    },
    enabled: debouncedQuery.length > 0,
  })

  const suggestedSearches = [
    'Industrial Automation companies',
    'Automotive Testing companies',
    'Industrial IoT companies',
    'Embedded Systems serving Automotive',
    'Robotics companies in Germany',
    'Manufacturing using Computer Vision',
    'Medical Device companies with AI',
    'companies serving Aerospace',
  ]

  return (
    <Box>
      <Typography variant="h4" fontWeight={600} gutterBottom>
        Semantic Search
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Search across companies, products, services, and news using natural language
      </Typography>

      {/* Search Bar */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <TextField
            fullWidth
            placeholder="Search for companies, products, services... (e.g., 'Industrial Automation companies serving Automotive')"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && setDebouncedQuery(query)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              sx: { fontSize: '1.1rem' },
            }}
            sx={{ mb: 2 }}
          />
          
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              size="small"
              placeholder="Industry"
              value={filters.industry}
              onChange={(e) => setFilters({ ...filters, industry: e.target.value })}
              sx={{ minWidth: 150 }}
            />
            <TextField
              size="small"
              placeholder="Domain"
              value={filters.domain}
              onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
              sx={{ minWidth: 150 }}
            />
            <TextField
              size="small"
              placeholder="Country"
              value={filters.country}
              onChange={(e) => setFilters({ ...filters, country: e.target.value })}
              sx={{ minWidth: 150 }}
            />
            <TextField
              size="small"
              placeholder="Technology"
              value={filters.technology}
              onChange={(e) => setFilters({ ...filters, technology: e.target.value })}
              sx={{ minWidth: 150 }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        sx={{ mb: 3 }}
      >
        <Tab label="All" />
        <Tab label="Companies" />
        <Tab label="Products" />
        <Tab label="Services" />
        <Tab label="News" />
      </Tabs>

      {/* Results */}
      {isLoading ? (
        <Grid container spacing={2}>
          {[1, 2, 3, 4, 5].map((i) => (
            <Grid item xs={12} key={i}>
              <Skeleton variant="rectangular" height={100} sx={{ borderRadius: 2 }} />
            </Grid>
          ))}
        </Grid>
      ) : searchResults?.results?.length > 0 ? (
        <Grid container spacing={2}>
          {searchResults.results.map((result: any, index: number) => (
            <Grid item xs={12} key={result.id || index}>
              <Card
                className="dashboard-card"
                sx={{ cursor: 'pointer' }}
                onClick={() => {
                  if (result.entity_type === 'company') {
                    navigate(`/companies/${result.id}`)
                  }
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="h6" fontWeight={600}>
                          {result.name}
                        </Typography>
                        <Chip label={result.entity_type} size="small" variant="outlined" />
                      </Box>
                      {result.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {result.description}
                        </Typography>
                      )}
                      {result.highlights?.map((highlight: string, i: number) => (
                        <Chip
                          key={i}
                          label={highlight}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                    <Box
                      sx={{
                        px: 2,
                        py: 1,
                        bgcolor: 'primary.main',
                        color: 'primary.contrastText',
                        borderRadius: 2,
                        fontWeight: 600,
                      }}
                    >
                      {(result.score * 100).toFixed(0)}%
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : debouncedQuery ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No results found for "{debouncedQuery}"
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Try different keywords or adjust your filters
          </Typography>
        </Paper>
      ) : (
        <Box>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Suggested Searches
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {suggestedSearches.map((search, i) => (
              <Chip
                key={i}
                label={search}
                onClick={() => {
                  setQuery(search)
                  setDebouncedQuery(search)
                }}
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>
        </Box>
      )}
    </Box>
  )
}

export default Search