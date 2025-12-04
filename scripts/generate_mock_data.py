"""
Generate realistic sample project data based on scraped market data
"""
import json
from pathlib import Path


def load_market_data(file_path: str) -> dict:
    """Load scraped market data"""
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_sample_projects(market_data: dict) -> list:
    """
    Generate 3 realistic project datasets based on Chakan market data

    Projects based on actual market leaders from scraped data
    """

    base_psf = market_data['pricing']['saleable_psf']  # ₹3551/sqft
    absorption_rates = market_data['absorption_rates']

    projects = [
        {
            "projectId": "P_CHAKAN_001",
            "projectName": "Sara City",
            "developer": {
                "developerId": "D_001",
                "developerName": "Sara Builders & Developers",
                "apfScore": 0.92,
                "marketabilityIndex": 0.88
            },
            "location": {
                "city": "Pune",
                "microMarket": "Chakan",
                "pincode": "410501"
            },

            # Layer 0: Raw Dimensions
            "totalUnits": 100,  # U
            "totalLandArea_sqft": 70000,  # L²
            "totalSaleableArea_sqft": 60000,
            "totalCarpetArea_sqft": 42000,
            "projectDuration_months": 36,  # T
            "totalProjectCost_inr": 500000000,  # CF (50 Cr)
            "launchDate": "2025-06-01",
            "completionDate": "2028-06-01",

            # Unit breakdown
            "units": [
                {
                    "unitType": "1BHK",
                    "count": 30,
                    "areaPerUnit_sqft": 500,  # Carpet
                    "saleablePerUnit_sqft": 600,
                    "pricePerUnit_inr": 3000000  # 30 lakhs (₹5000/sqft carpet)
                },
                {
                    "unitType": "2BHK",
                    "count": 50,
                    "areaPerUnit_sqft": 700,  # Carpet
                    "saleablePerUnit_sqft": 840,
                    "pricePerUnit_inr": 4200000  # 42 lakhs (₹6000/sqft carpet)
                },
                {
                    "unitType": "3BHK",
                    "count": 20,
                    "areaPerUnit_sqft": 1000,  # Carpet
                    "saleablePerUnit_sqft": 1200,
                    "pricePerUnit_inr": 6000000  # 60 lakhs (₹6000/sqft carpet)
                }
            ],

            # Market data from scraped HTML
            "marketData": {
                "absorptionRate_1BHK": absorption_rates['1BHK'],  # 3% per month
                "absorptionRate_2BHK": absorption_rates['2BHK'],  # 5% per month
                "absorptionRate_3BHK": absorption_rates['3BHK'],  # 2% per month
                "priceAppreciation_annual": 0.08,  # 8% per year
                "competitiveIntensity": "medium",
                "demandScore": 78
            },

            # Financial projections (Layer 2 inputs)
            "financials": {
                "initialInvestment": 500000000,  # 50 Cr
                "annualCashFlows": [125000000, 150000000, 175000000, 200000000, 225000000],  # 5 years
                "discountRate": 0.12,  # 12%
                "expectedIRR": 0.24,  # 24%
                "expectedNPV": 520000000  # 52 Cr
            }
        },

        {
            "projectId": "P_CHAKAN_002",
            "projectName": "Pradnyesh Shriniwas",
            "developer": {
                "developerId": "D_002",
                "developerName": "JJ Mauli Developers",
                "apfScore": 0.85,
                "marketabilityIndex": 0.80
            },
            "location": {
                "city": "Pune",
                "microMarket": "Chakan",
                "pincode": "410501"
            },

            # Layer 0: Raw Dimensions
            "totalUnits": 80,  # U (smaller project)
            "totalLandArea_sqft": 55000,  # L²
            "totalSaleableArea_sqft": 48000,
            "totalCarpetArea_sqft": 33600,
            "projectDuration_months": 30,  # T
            "totalProjectCost_inr": 400000000,  # CF (40 Cr)
            "launchDate": "2025-09-01",
            "completionDate": "2028-03-01",

            # Unit breakdown (more 1BHK focused)
            "units": [
                {
                    "unitType": "1BHK",
                    "count": 40,  # 50% of units
                    "areaPerUnit_sqft": 480,
                    "saleablePerUnit_sqft": 580,
                    "pricePerUnit_inr": 2900000  # 29 lakhs
                },
                {
                    "unitType": "2BHK",
                    "count": 30,  # 37.5%
                    "areaPerUnit_sqft": 680,
                    "saleablePerUnit_sqft": 820,
                    "pricePerUnit_inr": 4100000  # 41 lakhs
                },
                {
                    "unitType": "3BHK",
                    "count": 10,  # 12.5%
                    "areaPerUnit_sqft": 950,
                    "saleablePerUnit_sqft": 1140,
                    "pricePerUnit_inr": 5700000  # 57 lakhs
                }
            ],

            "marketData": {
                "absorptionRate_1BHK": 0.03,
                "absorptionRate_2BHK": 0.05,
                "absorptionRate_3BHK": 0.02,
                "priceAppreciation_annual": 0.08,
                "competitiveIntensity": "medium",
                "demandScore": 75
            },

            "financials": {
                "initialInvestment": 400000000,  # 40 Cr
                "annualCashFlows": [100000000, 120000000, 140000000, 160000000],  # 4 years
                "discountRate": 0.12,
                "expectedIRR": 0.22,  # 22%
                "expectedNPV": 410000000  # 41 Cr
            }
        },

        {
            "projectId": "P_CHAKAN_003",
            "projectName": "Sara Nilaay",
            "developer": {
                "developerId": "D_001",
                "developerName": "Sara Builders & Developers",
                "apfScore": 0.92,
                "marketabilityIndex": 0.88
            },
            "location": {
                "city": "Pune",
                "microMarket": "Chakan",
                "pincode": "410501"
            },

            # Layer 0: Raw Dimensions (larger premium project)
            "totalUnits": 120,  # U
            "totalLandArea_sqft": 90000,  # L²
            "totalSaleableArea_sqft": 78000,
            "totalCarpetArea_sqft": 54600,
            "projectDuration_months": 42,  # T (longer)
            "totalProjectCost_inr": 650000000,  # CF (65 Cr)
            "launchDate": "2025-03-01",
            "completionDate": "2028-09-01",

            # Unit breakdown (premium 2BHK & 3BHK focused)
            "units": [
                {
                    "unitType": "1BHK",
                    "count": 20,  # 16.7% (fewer 1BHK)
                    "areaPerUnit_sqft": 520,
                    "saleablePerUnit_sqft": 630,
                    "pricePerUnit_inr": 3150000  # 31.5 lakhs
                },
                {
                    "unitType": "2BHK",
                    "count": 70,  # 58.3% (majority)
                    "areaPerUnit_sqft": 720,
                    "saleablePerUnit_sqft": 870,
                    "pricePerUnit_inr": 4350000  # 43.5 lakhs
                },
                {
                    "unitType": "3BHK",
                    "count": 30,  # 25% (premium segment)
                    "areaPerUnit_sqft": 1050,
                    "saleablePerUnit_sqft": 1260,
                    "pricePerUnit_inr": 6300000  # 63 lakhs
                }
            ],

            "marketData": {
                "absorptionRate_1BHK": 0.03,
                "absorptionRate_2BHK": 0.05,
                "absorptionRate_3BHK": 0.02,
                "priceAppreciation_annual": 0.08,
                "competitiveIntensity": "medium",
                "demandScore": 82  # Higher demand
            },

            "financials": {
                "initialInvestment": 650000000,  # 65 Cr
                "annualCashFlows": [160000000, 195000000, 230000000, 265000000, 300000000],  # 5 years
                "discountRate": 0.12,
                "expectedIRR": 0.26,  # 26% (best performer)
                "expectedNPV": 675000000  # 67.5 Cr
            }
        }
    ]

    return projects


def generate_lf_mock_responses(market_data: dict):
    """Generate mock LF API responses for all 5 pillars"""

    # Pillar 1: Market Intelligence
    pillar1 = {
        "pillar": "1_market_intelligence",
        "location": "Chakan, Pune",
        "quarter": market_data['location']['quarter'],
        "dataVersion": market_data['location']['dataVersion'],
        "data": {
            "prices": {
                "saleable_psf": market_data['pricing']['saleable_psf'],
                "carpet_psf": market_data['pricing']['carpet_psf'],
                "trend": market_data['pricing']['trend'],
                "mom_change_percent": market_data['pricing']['mom_change_percent']
            },
            "absorption": {
                "monthly_units": market_data['sales']['monthly_units_avg'],
                "absorption_rate_percent": market_data['market_summary']['sales_velocity_percent'],
                "velocity_trend": "moderate"
            },
            "micromarket_eval": {
                "demand_score": market_data['market_insights']['demand_score'],
                "supply_pressure": market_data['market_insights']['supply_pressure'],
                "price_momentum": market_data['market_insights']['price_momentum']
            },
            "competitive_intensity": {
                "total_projects": market_data['market_summary']['total_projects'],
                "active_developers": market_data['market_summary']['active_developers'],
                "intensity_level": market_data['market_insights']['competitive_intensity']
            }
        }
    }

    # Pillar 2: Product Performance
    pillar2 = {
        "pillar": "2_product_performance",
        "location": "Chakan, Pune",
        "quarter": market_data['location']['quarter'],
        "data": {
            "typology_performance": {
                "1BHK": {
                    "absorption_rate_monthly": market_data['absorption_rates']['1BHK'],
                    "demand_level": "moderate",
                    "optimal_size_range_sqft": [450, 550]
                },
                "2BHK": {
                    "absorption_rate_monthly": market_data['absorption_rates']['2BHK'],
                    "demand_level": "high",
                    "optimal_size_range_sqft": [650, 750]
                },
                "3BHK": {
                    "absorption_rate_monthly": market_data['absorption_rates']['3BHK'],
                    "demand_level": "low",
                    "optimal_size_range_sqft": [950, 1100]
                }
            },
            "efficiency_metrics": {
                "carpet_to_saleable_ratio": 0.70,  # 70% efficiency
                "optimal_unit_mix": {
                    "1BHK": 0.25,
                    "2BHK": 0.50,
                    "3BHK": 0.25
                }
            }
        }
    }

    # Pillar 3: Developer Performance
    pillar3 = {
        "pillar": "3_developer_performance",
        "developers": market_data['top_developers'],
        "metrics": {
            "apf_definition": "Architect Performance Factor - measures delivery efficiency",
            "marketability_definition": "Market positioning and brand strength"
        }
    }

    # Pillar 4: Financial
    pillar4 = {
        "pillar": "4_financial",
        "location": "Chakan, Pune",
        "benchmarks": {
            "typical_irr_range": [0.20, 0.28],  # 20-28%
            "typical_payback_period_months": [24, 36],
            "discount_rate_standard": 0.12,  # 12%
            "price_appreciation_annual": 0.08  # 8%
        },
        "feasibility_thresholds": {
            "min_irr_percent": 18,
            "min_profitability_index": 1.0,
            "max_payback_period_months": 48
        }
    }

    # Pillar 5: Sales/Operations
    pillar5 = {
        "pillar": "5_sales_operations",
        "location": "Chakan, Pune",
        "sales_patterns": {
            "peak_sales_months": ["March", "April", "October", "November"],
            "average_sales_cycle_days": 45,
            "customer_segments": {
                "end_users": 0.65,
                "investors": 0.35
            }
        },
        "distribution_strategies": {
            "direct_sales": 0.60,
            "channel_partners": 0.40
        }
    }

    return {
        "pillar1_market": pillar1,
        "pillar2_product": pillar2,
        "pillar3_developer": pillar3,
        "pillar4_financial": pillar4,
        "pillar5_sales": pillar5
    }


def save_projects(projects: list, output_file: str):
    """Save project data to JSON"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(projects, f, indent=2)

    print(f"✓ Saved {len(projects)} projects to {output_file}")


def save_lf_responses(lf_data: dict, output_dir: str):
    """Save LF mock responses"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for filename, data in lf_data.items():
        file_path = output_path / f"{filename}.json"
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved {filename}.json")


def main():
    """Main execution"""
    market_data_file = "data/chakan_market_data.json"
    projects_output = "data/sample_projects.json"
    lf_responses_dir = "data/lf_mock_responses"

    print("Loading market data...")
    market_data = load_market_data(market_data_file)

    print("\nGenerating sample projects...")
    projects = generate_sample_projects(market_data)

    for project in projects:
        print(f"  - {project['projectName']} ({project['totalUnits']} units, "
              f"Expected IRR: {project['financials']['expectedIRR']*100:.1f}%)")

    print("\nGenerating LF mock API responses...")
    lf_data = generate_lf_mock_responses(market_data)
    print(f"  - Created {len(lf_data)} pillar responses")

    save_projects(projects, projects_output)
    save_lf_responses(lf_data, lf_responses_dir)

    print("\n✓ Mock data generation complete!")
    print(f"\nGenerated files:")
    print(f"  - {projects_output}")
    print(f"  - {lf_responses_dir}/*.json (5 files)")


if __name__ == "__main__":
    main()
