// =================================================================================================
//! @file close_pairs.c
//! @author STEER Framework Contributors
//! @brief This file implements the TestU01 Close Pairs test for the STEER framework.
//! @remarks Requires ANSI C99 (or better) compliant compilers.
//! @remarks Supported host operating systems: Any *nix
//! @copyright Copyright (c) 2024 Anametric, Inc. All rights reserved.
//!
//  Includes
// =================================================================================================
#include "steer.h"
#include "steer_json_utilities.h"
#include "steer_nist_sts_utilities_private.h"
#include "steer_parameters_info_utilities.h"
#include "steer_report_utilities.h"
#include "steer_report_utilities_private.h"
#include "steer_string_utilities.h"
#include "steer_string_utilities_private.h"
#include "steer_test_info_utilities.h"
#include "steer_test_shell.h"
#include "steer_utilities.h"
#include "steer_utilities_private.h"
#include "steer_value_utilities.h"
#include "cephes.h"
#include "defs.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

// =================================================================================================
//  Private constants
// =================================================================================================

#define PROGRAM_NAME        "testu01_close_pairs_test"
#define PROGRAM_VERSION     "0.1.0"
#define TEST_NAME           "close pairs"
#define TEST_DESCRIPTION \
"The Close Pairs test generates n points uniformly in [0,1)^t and computes all pairwise \
Euclidean distances. It counts the number of pairs Y closer than a threshold d_0. Under \
the null hypothesis, Y is approximately Poisson with a computable mean mu. The test \
standardizes Y and computes a P-value using the complementary error function. This test \
detects generators that produce points with anomalous clustering in low dimensions."
#define CONFIGURATION_COUNT         1
#define TESTU01_NAME                "TestU01 Crush Battery"

#define MINIMUM_BITSTREAM_COUNT     1
#define MINIMUM_BITSTREAM_LENGTH    131072
#define MINIMUM_SIGNIFICANCE_LEVEL  0.0
#define MAXIMUM_SIGNIFICANCE_LEVEL  1.0

// Close Pairs parameter defaults
#define CP_N_DEFAULT            2000    // Number of points
#define CP_T_DEFAULT            2       // Dimension
#define CP_D0           0.05    // Distance threshold
#define CP_BITS_PER_COORD  32   // Bits per coordinate

// =================================================================================================
//  Private types
// =================================================================================================

typedef struct ttestu01_closepairsprivatedata
{
    tSTEER_CliArguments*        cliArguments;
    tSTEER_ReportPtr            report;
    uint64_t                    bitstreamCount;
    uint64_t                    bitstreamLength;
    double                      significanceLevel;
    uint32_t                    significanceLevelPrecision;
    uint64_t                    minimumTestCountRequiredForSignificance;
    uint64_t                    predictedPassedTestCount;
    uint64_t                    predictedFailedTestCount;
    tSTEER_ConfigurationState   configurationState[CONFIGURATION_COUNT];
    uint64_t                    ones;
    uint64_t                    zeros;
    uint64_t                    numPoints;
    uint64_t                    dimension;
    int32_t                     closePairCount;
    double                      mu;
    double                      zScore;
    double                      probabilityValue;
}
tTestU01_ClosePairsPrivateData;

// =================================================================================================
//  Private globals
// =================================================================================================

static tSTEER_InfoList gReferences = {
    1,
    {
        "P. L'Ecuyer and R. Simard, TestU01: A C Library for Empirical Testing of Random Number Generators, ACM TOMACS, 2007"
    }
};

static tSTEER_InfoList gAuthors = {
    2,
    {
        "Pierre L'Ecuyer",
        "Richard Simard"
    }
};

static tSTEER_InfoList gContributors = {
    1,
    {
        STEER_CONTRIBUTOR_GARY_WOODCOCK
    }
};

static tSTEER_InfoList gMaintainers = {
    2,
    {
        STEER_MAINTAINER_ANAMETRIC,
        STEER_MAINTAINER_SMU_DARWIN_DEASON
    }
};

static tSTEER_TestInfo gTestInfo = {
    TEST_NAME,
    TESTU01_NAME,
    TEST_DESCRIPTION,
    eSTEER_Complexity_Average,
    &gReferences,
    PROGRAM_NAME,
    PROGRAM_VERSION,
    eSTEER_InputFormat_Bitstream,
    STEER_REPOSITORY_URI,
    &gAuthors,
    &gContributors,
    &gMaintainers,
    STEER_CONTACT
};

static tSTEER_ParameterInfoList gParameterInfoList = {
    5,
    {
        {
            STEER_JSON_TAG_BITSTREAM_COUNT,
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            STEER_JSON_VALUE_BITSTREAMS,
            "1",
            "1",
            NULL
        },
        {
            STEER_JSON_TAG_BITSTREAM_LENGTH,
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            STEER_JSON_VALUE_BITS,
            "1000000",
            "131072",
            NULL
        },
        {
            STEER_JSON_TAG_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
            NULL,
            STEER_JSON_VALUE_DEFAULT_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_MINIMUM_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_MAXIMUM_SIGNIFICANCE_LEVEL
        },
        {
            "num points",
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            NULL,
            "2000",
            "100",
            "50000"
        },
        {
            "dimension",
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            NULL,
            "2",
            "2",
            "5"
        }
    }
};

static tSTEER_ParametersInfo gParametersInfo = {
    TEST_NAME,
    &gParameterInfoList
};

// =================================================================================================
//  Helper: extract 32-bit integer from bitstream at given bit offset
// =================================================================================================
static uint32_t ExtractBits(uint8_t* buffer, uint64_t bitOffset, int numBits)
{
    uint32_t value = 0;
    int i;
    for (i = 0; i < numBits; i++)
        value = (value << 1) | buffer[bitOffset + i];
    return value;
}

// =================================================================================================
//  RunTest
// =================================================================================================
int32_t RunTest(tTestU01_ClosePairsPrivateData* privateData,
                uint8_t* bitstreamBuffer,
                bool* passed)
{
    int32_t result = STEER_RESULT_SUCCESS;
    double* points = NULL;
    uint64_t maxPoints;
    uint64_t n;
    int32_t closePairs = 0;
    double mu, zScore;
    double vt, d0t;
    uint64_t i, j;
    uint64_t cpN = privateData->numPoints;
    uint64_t cpT = privateData->dimension;

    // Determine how many points we can generate
    // Each point needs cpT coordinates, each coordinate needs CP_BITS_PER_COORD bits
    maxPoints = privateData->bitstreamLength / (cpT * CP_BITS_PER_COORD);
    n = (maxPoints > cpN) ? cpN : maxPoints;

    // Allocate points array
    result = STEER_AllocateMemory(n * cpT * sizeof(double), (void**)&points);
    if (result != STEER_RESULT_SUCCESS)
        return result;

    // Extract points as coordinates in [0,1)
    for (i = 0; i < n; i++)
    {
        uint64_t d;
        for (d = 0; d < cpT; d++)
        {
            uint32_t raw = ExtractBits(bitstreamBuffer,
                                       (i * cpT + d) * CP_BITS_PER_COORD,
                                       CP_BITS_PER_COORD);
            points[i * cpT + d] = (double)raw / 4294967296.0;  // 2^32
        }
    }

    // Count close pairs (distance < d_0)
    closePairs = 0;
    for (i = 0; i < n; i++)
    {
        for (j = i + 1; j < n; j++)
        {
            double dist2 = 0.0;
            uint64_t d;
            for (d = 0; d < cpT; d++)
            {
                double diff = points[i * cpT + d] - points[j * cpT + d];
                dist2 += diff * diff;
            }
            if (sqrt(dist2) < CP_D0)
                closePairs++;
        }
    }

    // Compute expected value mu
    // V_t = pi^(t/2) / Gamma(t/2 + 1) -- for t=2: V_2 = pi
    // mu = n*(n-1)/2 * V_t * d_0^t
    vt = pow(M_PI, (double)cpT / 2.0) / tgamma((double)cpT / 2.0 + 1.0);
    d0t = pow(CP_D0, (double)cpT);
    mu = (double)n * ((double)n - 1.0) / 2.0 * vt * d0t;

    // Standardize: Z = (Y - mu) / sqrt(mu)
    zScore = ((double)closePairs - mu) / sqrt(mu);

    privateData->closePairCount = closePairs;
    privateData->mu = mu;
    privateData->zScore = zScore;

    // P-value via complementary error function: erfc(|Z|/sqrt(2))
    privateData->probabilityValue = erfc(fabs(zScore) / sqrt(2.0));

    *passed = (privateData->probabilityValue >= privateData->significanceLevel);

    STEER_FreeMemory((void**)&points);
    return result;
}

// =================================================================================================
//  GetTestInfo
// =================================================================================================
char* GetTestInfo(void)
{
    char* json = NULL;
    int32_t result = STEER_TestInfoToJson(&gTestInfo, &json);
    if (result == STEER_RESULT_SUCCESS)
        return json;
    else
        return NULL;
}

// =================================================================================================
//  GetParametersInfo
// =================================================================================================
char* GetParametersInfo(void)
{
    char* json = NULL;
    int32_t result = STEER_ParametersInfoToJson(&gParametersInfo, &json);
    if (result == STEER_RESULT_SUCCESS)
        return json;
    else
        return NULL;
}

// =================================================================================================
//  InitTest
// =================================================================================================
int32_t InitTest(tSTEER_CliArguments* cliArguments,
                 tSTEER_ParameterSet* parameters,
                 void** testPrivateData,
                 uint64_t* bufferSizeInBytes)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_ClosePairsPrivateData* privData = NULL;

    *testPrivateData = NULL;
    *bufferSizeInBytes = 0;

    result = STEER_AllocateMemory(sizeof(tTestU01_ClosePairsPrivateData), (void**)&privData);

    if (result == STEER_RESULT_SUCCESS)
    {
        uint_fast32_t i = 0;
        void* nativeValue = NULL;

        privData->cliArguments = cliArguments;

        // Set defaults for configurable parameters
        privData->numPoints = CP_N_DEFAULT;
        privData->dimension = CP_T_DEFAULT;

        for (i = 0; i < parameters->count; i++)
        {
            if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_BITSTREAM_COUNT) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->bitstreamCount = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_BITSTREAM_LENGTH) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->bitstreamLength = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_SIGNIFICANCE_LEVEL) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->significanceLevel = *((double*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
                if (result == STEER_RESULT_SUCCESS)
                {
                    if (parameters->parameter[i].precision != NULL)
                        result = STEER_ConvertStringToUnsigned32BitInteger(
                            parameters->parameter[i].precision,
                            &(privData->significanceLevelPrecision));
                }
            }
            else if (strcmp(parameters->parameter[i].name, "num points") == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->numPoints = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, "dimension") == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->dimension = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            if (result != STEER_RESULT_SUCCESS) break;
        }

        if ((privData->bitstreamCount < MINIMUM_BITSTREAM_COUNT) ||
            (privData->bitstreamLength < MINIMUM_BITSTREAM_LENGTH) ||
            ((privData->bitstreamLength % 8) != 0) ||
            (privData->significanceLevel <= MINIMUM_SIGNIFICANCE_LEVEL) ||
            (privData->significanceLevel >= MAXIMUM_SIGNIFICANCE_LEVEL))
        {
            result = STEER_CHECK_ERROR(EINVAL);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_GetMinimumTestCount(privData->significanceLevel,
                                               privData->bitstreamCount,
                                               &(privData->minimumTestCountRequiredForSignificance),
                                               &(privData->predictedPassedTestCount),
                                               &(privData->predictedFailedTestCount));
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            privData->configurationState[0].configurationId = 0;
            *testPrivateData = (void*)privData;
            *bufferSizeInBytes = privData->bitstreamLength / 8;
        }
    }

    if (result != STEER_RESULT_SUCCESS)
        STEER_FreeMemory((void**)&privData);
    return result;
}

// =================================================================================================
//  GetConfigurationCount
// =================================================================================================
uint32_t GetConfigurationCount(void* testPrivateData)
{
    return CONFIGURATION_COUNT;
}

// =================================================================================================
//  SetReport
// =================================================================================================
int32_t SetReport(void* testPrivateData, tSTEER_ReportPtr report)
{
    ((tTestU01_ClosePairsPrivateData*)testPrivateData)->report = report;
    return STEER_RESULT_SUCCESS;
}

// =================================================================================================
//  ExecuteTest
// =================================================================================================
int32_t ExecuteTest(void* testPrivateData,
                    const char* bitstreamId,
                    uint8_t* buffer,
                    uint64_t bufferSizeInBytes,
                    uint64_t bytesInBuffer,
                    uint64_t numZeros,
                    uint64_t numOnes)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_ClosePairsPrivateData* privData = (tTestU01_ClosePairsPrivateData*)testPrivateData;
    bool passed = false;
    char calculationStr[STEER_STRING_MAX_LENGTH] = { 0 };
    char criterionStr[STEER_STRING_MAX_LENGTH] = { 0 };
    uint64_t testId = 0;
    char* end = NULL;

    testId = strtoull(bitstreamId, &end, 0) - 1;

    privData->ones = numOnes;
    privData->zeros = numZeros;
    privData->configurationState[0].accumulatedOnes += numOnes;
    privData->configurationState[0].accumulatedZeros += numZeros;

    result = RunTest(privData, buffer, &passed);

    // Add calculations
    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%" PRIu64 "", numOnes);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_ONES,
                                            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
                                            NULL, STEER_JSON_VALUE_BITS, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%" PRIu64 "", numZeros);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_ZEROS,
                                            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
                                            NULL, STEER_JSON_VALUE_BITS, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%d", privData->closePairCount);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            "close pair count",
                                            STEER_JSON_VALUE_SIGNED_32_BIT_INTEGER,
                                            NULL, NULL, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->mu);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            "mu",
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->zScore);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            "z score",
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->probabilityValue);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_PROBABILITY_VALUE,
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    // Add criteria
    if (result == STEER_RESULT_SUCCESS)
    {
        memset(criterionStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(criterionStr, "%s of %.*f >= %s of %.*f",
                STEER_JSON_TAG_PROBABILITY_VALUE,
                STEER_DEFAULT_FLOATING_POINT_PRECISION,
                privData->probabilityValue,
                STEER_JSON_TAG_SIGNIFICANCE_LEVEL,
                privData->significanceLevelPrecision,
                privData->significanceLevel);
        result = STEER_AddCriterionToTest(privData->report, 0, testId, criterionStr,
                                          (privData->probabilityValue >= privData->significanceLevel));
    }

    // Add evaluation
    if (result == STEER_RESULT_SUCCESS)
    {
        bool eval_passed = false;
        result = STEER_AddEvaluationToTest(privData->report, 0, testId, &eval_passed);
        if (result == STEER_RESULT_SUCCESS)
        {
            privData->configurationState[0].testsRun++;
            if (eval_passed)
                privData->configurationState[0].testsPassed++;
            else
                privData->configurationState[0].testsFailed++;
        }
    }

    STEER_FreeMemory((void**)&buffer);
    return result;
}

// =================================================================================================
//  FinalizeTest
// =================================================================================================
int32_t FinalizeTest(void** testPrivateData, uint64_t suppliedNumberOfBitstreams)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_ClosePairsPrivateData* privData = (tTestU01_ClosePairsPrivateData*)(*testPrivateData);

    if (privData != NULL)
    {
        double probabilityValueUniformity = 0.0;
        uint64_t proportionThresholdMinimum = 0;
        uint64_t proportionThresholdMaximum = 0;

        result = STEER_NistStsAddRequiredMetricsToConfiguration(privData->report, 0,
                    suppliedNumberOfBitstreams,
                    privData->minimumTestCountRequiredForSignificance,
                    privData->configurationState[0].testsPassed,
                    privData->predictedPassedTestCount,
                    privData->configurationState[0].accumulatedOnes,
                    privData->configurationState[0].accumulatedZeros);

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddMetricsToConfiguration(privData->report, 0, false,
                        suppliedNumberOfBitstreams, privData->significanceLevel,
                        &probabilityValueUniformity,
                        &proportionThresholdMinimum, &proportionThresholdMaximum);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_AddConfusionMatrixMetricsToConfiguration(privData->report, 0,
                        privData->minimumTestCountRequiredForSignificance,
                        privData->configurationState[0].testsRun,
                        privData->configurationState[0].testsPassed,
                        privData->configurationState[0].testsFailed,
                        privData->predictedPassedTestCount,
                        privData->predictedFailedTestCount);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddRequiredCriterionToConfiguration(privData->report, 0,
                        suppliedNumberOfBitstreams,
                        privData->configurationState[0].testsPassed,
                        privData->significanceLevel,
                        privData->significanceLevelPrecision,
                        privData->minimumTestCountRequiredForSignificance);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddCriteriaToConfiguration(privData->report, 0,
                        probabilityValueUniformity,
                        proportionThresholdMinimum, proportionThresholdMaximum,
                        privData->configurationState[0].testsRun,
                        privData->configurationState[0].testsPassed);
        }

        if (result == STEER_RESULT_SUCCESS)
            result = STEER_AddEvaluationToConfiguration(privData->report, 0);

        STEER_FreeMemory((void**)testPrivateData);
    }
    return result;
}

// =================================================================================================
//  main
// =================================================================================================
int main(int argc, const char* argv[])
{
    return STEER_Run(PROGRAM_NAME, argc, argv,
                     GetTestInfo, GetParametersInfo,
                     InitTest, GetConfigurationCount,
                     SetReport, ExecuteTest, FinalizeTest);
}

// =================================================================================================
